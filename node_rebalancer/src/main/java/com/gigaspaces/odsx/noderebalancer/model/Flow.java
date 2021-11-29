package com.gigaspaces.odsx.noderebalancer.model;

import com.gigaspaces.odsx.noderebalancer.action.BaseAction;
import com.gigaspaces.odsx.noderebalancer.event.Event;
import com.gigaspaces.odsx.noderebalancer.action.Status;
import com.gigaspaces.odsx.noderebalancer.event.EventDescrirptor;
import com.gigaspaces.odsx.noderebalancer.event.FlowEventPublisher;
import com.gigaspaces.odsx.noderebalancer.policy.ServerConfiguration;

import java.util.*;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.Future;
import java.util.concurrent.ScheduledFuture;
import java.util.logging.Logger;

public abstract class Flow implements FlowEventPublisher {

    /**
     * Parameters  for this flow, comes from configuration.
     */
    private HashMap<String, String> parameters;

    /**
     * Server Information: IP Address, Container zone and count
     */
    private ServerConfiguration serverConfiguration;

    public abstract void updateStatistics(String hostAddress, Event event);

    /**
     * Internal Events during the flow execution, against which
     * a trigger can be written (to carry out actions).
    */
    public enum EventCode {
        ENTERING_STATE(10001),
        ASYNC_TIMER_COMPLETED(10002);
        public final int code;
        EventCode(int code){
            this.code = code;
        }
    }

    /**
     * Internal states a workflow can be in. This is different from the application or recovery specific states that the
     * concrete implementations define.
     */
    public enum WorkflowStatus{
        NOT_STARTED,
        ENTERING_STATE,
        WAIT_WHILE_ACTION_EXECUTION,
        WAIT_WHILE_SYNCHRONOUS_DELAY,
        WAIT,
        TRANSITION
    };

    /**
     * Track current status of this flow
     */
    //TODO: Ensure thread-safe access
    WorkflowStatus currentWorkflowStatus;

    private static final String FLOW_CONTEXT = "FLOW_CONTEXT" ;

    private String name;

    private State initialState;

    /**
     * States defined for this flow , in the concrete class.
     */
    private List<State> states;

    /**
     * Current state the flow is in. This is one of the states defined in the concrete Flow class.
     */
    State currentState;

    /**
     * Events dispatched for this flow accumulates here until they are processed. Processing involves finding if there
     * the event can be mapped to a trigger and if yes, then activate the trigger.
     */
    private ConcurrentLinkedQueue<Event> eventQueue;

    /**
     * Name Value pair to store information that could be shared by various actions in this Flow.
     */
    protected Context context;

    /**
     * List of actions to be executed as activation of a trigger for this flow.
     */
    Queue<BaseAction> pendingActionQueue;

    /**
     * Future representing outcome of the current or last action executed by the executor thread.
     */
    Future<?> pendingActionFuture;

    protected static Logger logger = Logger.getLogger(Flow.class.getName());



    public Flow(String name){
        this.name = name;
        states = new ArrayList<State>();
        pendingActionQueue = new ConcurrentLinkedQueue<BaseAction>();
        eventQueue = new ConcurrentLinkedQueue<Event>();
        currentWorkflowStatus = WorkflowStatus.NOT_STARTED;
        context = new Context(FLOW_CONTEXT, this::enqueue);
    }

    public String getName() {
        if(name != null) {
            return name;
        }
        return "Anonymous Flow of type : " + this.getClass();
    }

    public Context getContext() {
        return context;
    }

    /**
     * Are we waiting
     * Checks if currently a scheduled future is pending completion.
     * @return
     */
    public boolean isDelayPeriodOver() {
        boolean delayPeriodOver = true;
        Future<?> future = this.getFuture();
        if(future != null && (future instanceof ScheduledFuture) && !future.isDone() ){
            delayPeriodOver = false;
        }
        return  delayPeriodOver;
    }

    public void setServerConfiguration(ServerConfiguration serverConfiguration) {
        this.serverConfiguration = serverConfiguration;
        context.setServerConfiguration(serverConfiguration);
    }

    public void setParameters(Map<String, String> params) {
        this.parameters = new HashMap<>(params);
    }

    public String getParameter(String parameter){
        return parameters.get(parameter);
    }

    public Long getLongParameter(String parameter, Long defaultValue){
        String value = getParameter(parameter);
        Long result;

        if(value == null){
            logger.warning(" No value found for the parameter %s, the default value %s will be used.". format(parameter, defaultValue));
            result = defaultValue;
        } else {
            try{
                result = Long.valueOf(value);
            }catch(NumberFormatException nfe){
                logger.warning(" Number format exception while obtaining parameter %s value %s. Default will be used.". format(parameter, value));
                result = defaultValue;
            }
        }
        return result;
    }

    public void enqueue(Event event) {
        eventQueue.offer(event);
        logger.info("Added event to the queue : " + event);
    }


    public void setFuture(Future<Status> actionFuture) {
        pendingActionFuture = actionFuture;
    }

    /**
     * Transition to another workflow state.
     * When this occurs,
     * 1. All the pending event in the event queue will be flushed.
     * 2. Any remaining actions in the action list will be flushed.
     * @param targetState
     */
    public void transitionTo(String targetState) {
        WorkflowStatus previousWorkflowStatus = getWorkflowStatus();
        setCurrentWorkflowStatus(WorkflowStatus.TRANSITION);
        logger.info(String.format("Transitioning state. Current state %s. Target state %s", currentState, targetState));
        for(State state : states){
            if(state.getName().equals(targetState)){
                logger.info(String.format(" Updating Workflow Status from : %s to %s",currentWorkflowStatus,WorkflowStatus.ENTERING_STATE ) );
                setCurrentWorkflowStatus(WorkflowStatus.ENTERING_STATE);

                if(!pendingActionQueue.isEmpty()){
                    while(!pendingActionQueue.isEmpty()){
                        BaseAction removedAction = pendingActionQueue.remove();
                        logger.info(" Removing actions from previous state due to transition to new state : " + removedAction);
                    }
                    logger.info("There are no pending actions, queue flushed.");
                }


                if(!eventQueue.isEmpty()){
                    while(!eventQueue.isEmpty()){
                        Event removedEvent = eventQueue.remove();
                        logger.info(" Removing event from previous state due to transition to new state : " + removedEvent);
                    }
                    logger.info("There are no pending events, queue flushed.");
                }

                if(pendingActionFuture != null && !pendingActionFuture.isDone()){
                    logger.warning(String.format("Detected an incomplete action while transitioning state : from %s to %s , pendingFuture = %s",  currentState, targetState ,pendingActionFuture ));
                }
                pendingActionFuture = null;

                currentState = state;

                /**
                 * Generating event to indicate that a state transition is occurred.
                 * Since this is immediately after flushing the queue, this will be the first event that will be processed
                 * for the new state. Thus, if any trigger is defined for the event, it will be the first to trigger.
                 */
                Event event = new Event(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL,EventCode.ENTERING_STATE.code ), targetState);
                eventQueue.offer(event);
                logger.info("Added the state transition event : " + event);
                logger.info(String.format(" Updating Workflow Status from : %s to %s",currentWorkflowStatus,WorkflowStatus.WAIT ) );
                setCurrentWorkflowStatus(WorkflowStatus.WAIT);
                return;
            }
        }
        logger.severe("Could not transition to target state, possible misconfiguration. No target state matching : " + targetState);
    }


    /**
     * Provides current status of this workflow.
     * @See WorkflowStatus.
     * @return
     */
    public WorkflowStatus getWorkflowStatus() {
        return currentWorkflowStatus;
    }


    private void setCurrentWorkflowStatus(WorkflowStatus status) {
        this.currentWorkflowStatus = status;

    }

    /**
     * Change workflow status to indicate that action execution is completed
     */
    public void setStatusActionExecutionCompleted() {
        if(currentWorkflowStatus == WorkflowStatus.WAIT_WHILE_ACTION_EXECUTION){
            setCurrentWorkflowStatus(WorkflowStatus.WAIT);
        }else {
            logger.warning("Attempted to change workflow status to WAIT after action execution complete, but found the state to be : " + getWorkflowStatus());
        }
    }

    public void setStatusDelayExecutionStart() {
        setCurrentWorkflowStatus(WorkflowStatus.WAIT_WHILE_SYNCHRONOUS_DELAY);
    }
    public void setStatusDelayExecutionEnd() {
        setCurrentWorkflowStatus(WorkflowStatus.WAIT_WHILE_ACTION_EXECUTION);
    }
    /**
     * State of the latest action executed for this workflow.
     * @return
     */
    public Future<?> getFuture() {
        return pendingActionFuture;
    }

    /**
     * Provide next action to execute for this flow.
     * If there is no action remaining to execute, this method will change the workflow status so that event processing can resume
     * @return next action from queue or null
     */
    public BaseAction getNextAction() {
        BaseAction action = null;
        if ( pendingActionQueue == null){
            logger.warning("Got null pending action queue while obtaining next action to execute in the workflow " + this);
        }else if (pendingActionQueue.isEmpty()){
            logger.info("Action queue is empty.");
            setStatusActionExecutionCompleted();
        }else{
            action = pendingActionQueue.remove();
            if ( WorkflowStatus.WAIT_WHILE_ACTION_EXECUTION != getWorkflowStatus()) {
                logger.warning(String.format(" Expecting workflows status to be WAIT_WHILE_ACTION_EXECUTION, instead found %s. Changing it to expected value", currentWorkflowStatus));
                setCurrentWorkflowStatus(WorkflowStatus.WAIT_WHILE_ACTION_EXECUTION);
            }
        }
        return action;
    }




    public void processEvents() {
        if(! eventQueue.isEmpty()){
            Event event = eventQueue.poll();
            mapEventToTrigger(event, currentState);
        }
    }

    private void mapEventToTrigger(Event event, State currentState) {
        //TODO: logger.info()
        int count = 0;
        for (Trigger trigger : currentState.triggers){
            if(trigger.canRespondTo(event)){
                logger.info("Firing trigger in response to event " + event.getDescriptor());
                fireTrigger(trigger,currentState, event);
                count++;
            }
        }
        if( count == 0){
            logger.info("No triggers registered for the event, will be ignored : " + event);
        } else if (count > 1){
            //TODO: Should this scenario ever happen ? Desirable ? If no, we should have trigger map instead of list.
            logger.warning(" Multiple triggers registered for the event " + event);
        }
    }

    private void fireTrigger(Trigger trigger, State currentState, Event event) {
        if( trigger.getActionList() != null && trigger.getActionList().size() > 0){
            logger.info("Adding action(s) for the trigger  " + trigger);

            //guard check - we expect action queue to be empty / null at this point
            //TODO: Comment explaining pending action queue
            if(pendingActionQueue !=null && !pendingActionQueue.isEmpty() ){
                logger.severe(String.format("  %s  : State transition problem, event %s being processed even while non-empty action queue", getName(),event, pendingActionQueue));
            }
                //Considerations: trigger event to action mapping might be arbitrary.
            LinkedList<BaseAction> actionList =  new LinkedList<>(  trigger.getActionList());
            for(BaseAction action : actionList){
                action.setEvent(event);
            }
            pendingActionQueue = (Queue<BaseAction>) actionList;
            setCurrentWorkflowStatus(WorkflowStatus.WAIT_WHILE_ACTION_EXECUTION);
        } else{
            logger.warning( ()->("No actions configured for the trigger " + trigger));
        }

    }


    public void start(){
        if(currentWorkflowStatus == WorkflowStatus.NOT_STARTED){
            transitionTo(initialState.name);
        } else {
            throw  new IllegalStateException("Can not start a workflow that is already running.");
        }
        logger.info("Started the workflow,  current state is: " + currentState);
    }



    protected void addState(State state) {
        states.add(state);
        logger.info("Added state : " + state);

    }

    protected void setInitialState(State initialState) {
        this.initialState = initialState;
        currentState = initialState;
        logger.info("Set initial state : " + initialState);
    }


}
