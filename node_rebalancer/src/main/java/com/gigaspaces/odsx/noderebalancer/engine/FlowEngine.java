package com.gigaspaces.odsx.noderebalancer.engine;

import com.gigaspaces.odsx.noderebalancer.action.*;
import com.gigaspaces.odsx.noderebalancer.admin.AdminAdapter;
import com.gigaspaces.odsx.noderebalancer.admin.model.ContainerConfiguration;
import com.gigaspaces.odsx.noderebalancer.policy.Policy;
import com.gigaspaces.odsx.noderebalancer.policy.PolicyAssociation;
import com.gigaspaces.odsx.noderebalancer.policy.PolicyConfiguration;
import com.gigaspaces.odsx.noderebalancer.policy.ServerConfiguration;
import com.gigaspaces.odsx.noderebalancer.event.Event;
import com.gigaspaces.odsx.noderebalancer.event.EventDispatcher;
import com.gigaspaces.odsx.noderebalancer.model.Flow;
import com.gigaspaces.odsx.noderebalancer.util.BannerPrinter;


import javax.annotation.PreDestroy;
import java.util.*;
import java.util.concurrent.*;
import java.util.logging.Level;
import java.util.logging.Logger;

public class FlowEngine implements EventDispatcher {

    //TODO: THe thread pool size to be configured externally
    private static final int TASK_THREAD_POOL_SIZE = 5;
    private static final int TIMER_THREAD_POOL_SIZE = 2;

    /**
     * Collection of all the workflows configured.
     */
    List<Flow> flows;

    /**
     * Provide mapping from Node IP Address to workflow(recovery flow) for the node.
     */
    Map<String, Flow> machineToFlowMapping;

    /**
     * Timer and Delay actions  in Flow are executed on the task executor
    */
    ScheduledExecutorService scheduledExecutorService;

    /**
     * Flow level actions are executed on the task executor
     */
    ExecutorService taskExecutorService;

    /**
     * Policy declaration about various recovery flow depending on server type.
     */
    private PolicyConfiguration policyConfiguration;

    //TODO:Remove as no longer necessary
    /**
     * Used to put Container Configuration in a thread safe way.
     */
    ThreadLocal<ContainerConfiguration> threadLocalContainerConfiguration = new ThreadLocal<>();

    /**
     * Used to determine if it is time to shutdown
     */
    private volatile boolean runIndicator = true;

    Logger logger = Logger.getLogger(FlowEngine.class.getName());

    BannerPrinter bannerPrinter = new BannerPrinter();

    /**
     * Create the flow engine and build the workflow as per the policy configuration supplied.
     * @param configuration The policy configuration consisting of Policy definition and its assoicatin iwth nodes.
     *   Typically, the configuration information resides in cluster configuration file and a reader be used to read it.
     */
    public FlowEngine( PolicyConfiguration configuration){
        this.policyConfiguration = configuration;
        flows = new ArrayList<>();
        machineToFlowMapping = new HashMap<String, Flow>();
        buildWorkflows();
        //TODO: Extern the thread count
        scheduledExecutorService = Executors.newScheduledThreadPool(TIMER_THREAD_POOL_SIZE);
        taskExecutorService = Executors.newFixedThreadPool(TASK_THREAD_POOL_SIZE);
    }

    /**
     * Construct the recovery flow instances as per the policy configuration supplied.
     */
    private void buildWorkflows() {

        for(PolicyAssociation declaration : policyConfiguration.getPolicyAssociations()){
            Policy policy = declaration.getPolicy();
            String targetType = declaration.getTargetType();
            List<ServerConfiguration> serverConfigurations = declaration.getServerConfigurations();
            for(ServerConfiguration serverConfiguration: serverConfigurations){
                Flow flow = FlowBuilder.build(policy.getDefinition(), policy.getName(), serverConfiguration.getIpAddress(), policy.getParameters());
                flow.setServerConfiguration(serverConfiguration);
                flows.add(flow);
                machineToFlowMapping.put (serverConfiguration.getIpAddress(), flow);
            }
        }

    }


    /**
     * The main event loop
     * Before this
     *  Initialize workflows
     *  Create workflow instances, initialize them
     *  Initialize EventCode infra
     */
    public void run(){

        //Start workflows
        for(Flow flow : flows){
            //Get running actions for the flow
            flow.start();
        }

        while(runIndicator){
            try {
                for(Flow flow : flows){
                    processFlow(flow);
                }
                //TODO: Externalize wait period
                Thread.sleep(10);

            } catch (InterruptedException e) {
                logger.warning(" Exception while processing the recovery flow : " + e);
            }

        }

        shutDown();
    }

    /**
     * Examine the current status ( indicating a state of meta-state-machine common to all recovery flows),
     * and carry out action accordingly.
     * All recovery flow are in on of these states:
     *         NOT_STARTED - The flow is inactive
     *         WAIT_WHILE_ACTION_EXECUTION - Actions (in response to event -> trigger) are being carried out
     *         WAIT - Waiting for events to occur
     *         TRANSITION - Transitioning between states
     * @param flow
     */
    private void processFlow(Flow flow) {
        switch(flow.getWorkflowStatus()){
            case WAIT_WHILE_ACTION_EXECUTION:
                if( Level.FINE.equals(logger.getLevel()) ){
                    logger.fine(flow.getName() + " : Execution -  in WAIT_WHILE_ACTION_EXECUTION");
                }
                executeNextAction(flow);
                break;
            case WAIT_WHILE_SYNCHRONOUS_DELAY:
                if(flow.isDelayPeriodOver()){
                    logger.fine(flow.getName() + " : Execution -  in WAIT_WHILE_SYNCHRONOUS_DELAY - completed wait.");
                    flow.setStatusDelayExecutionEnd();
                }else {
                    if( Level.FINE.equals(logger.getLevel()) ){
                        logger.fine(flow.getName() + " : Execution -  in WAIT_WHILE_SYNCHRONOUS_DELAY - waiting.");
                    }
                }
                break;
            case WAIT:
                flow.processEvents();
                break;
            case TRANSITION:
                logger.info(flow.getName() + " : Execution -  in TRANSITION -to another state.");
                break;
            default:
                logger.warning(flow.getName() + " : Execution -  Unrecognized flow state - please check..");
                break;
        }
    }


    private void executeNextAction(Flow flow) {
        Future<?> future= flow.getFuture();
        if((future == null) || future.isDone()){
            BaseAction action = flow.getNextAction();
            if(action != null){
                if(action.getType() == BaseAction.Type.TASK){
                    logger.info("Running task : " + action);
                    Future<Status> actionFuture = taskExecutorService.submit(action);
                    flow.setFuture(actionFuture);
                }else if(action.getType() == BaseAction.Type.TIME){
                    if(action instanceof DelayAction){
                        logger.info("Running  Delay task : " + action);
                        DelayAction delayAction = (DelayAction) action;
                        ScheduledFuture<Status> scheduledFuture = scheduledExecutorService.schedule(delayAction, delayAction.getDelay(), TimeUnit.MILLISECONDS);
                        flow.setFuture(scheduledFuture);
                        flow.setStatusDelayExecutionStart();
                        logger.info(String.format("Will wait for %s ms due to synchronous delay action.", delayAction.getDelay()));
                    }else if(action instanceof TimerAction) {
                        TimerAction timerAction = (TimerAction) action;
                        ScheduledFuture<Status> scheduledFuture = scheduledExecutorService.schedule(timerAction, timerAction.getDelay(), TimeUnit.MILLISECONDS);
                        logger.info("Scheduled asynchronous timer for duration (ms) " + timerAction.getDelay());
                        // Asynchronous timer - When the time is elapsed, the Timer action will be executed and publish a timer event.
                    }else {
                            logger.warning("Incorrect configuration - Unsupported TIME action. Expected DelayAction or TimerAction, got : " + action);
                    }
                } else if(action.getType() == BaseAction.Type.FLOW){
                    if(action instanceof TransitionAction){
                        //TODO: On successfull transition, kill any pending timer
                        if(action instanceof ConditionalTransitionAction){
                            //Transition only if the condition evaluates to true, as reflected in successful status
                            Status status = Status.FAILURE;
                            try{
                                status = action.call();
                            }catch (Exception ex){
                                logger.warning("Exception encountered while evaluating conditional action " + action);
                                logger.log(Level.WARNING, "Exception is : ", ex);
                            }
                            if(status == Status.SUCCESS){
                                bannerPrinter.print(" Running transition action, transitioning to State : " + ((TransitionAction)action).getTargetState());
                                flow.transitionTo(((TransitionAction)action).getTargetState());
                            }
                        } else {
                            //Transition unconditionally
                            bannerPrinter.print(" Running transition action, transitioning to State : " + ((TransitionAction)action).getTargetState());
                            flow.transitionTo(((TransitionAction)action).getTargetState());
                        }
                    } else {
                        logger.warning(" Unsupported FLOW action :  " + action );
                    }
                }
            }else {
                logger.info("Got null action ");
            }
        }
    }


    @Override
    public  void dispatchEvent(String hostAddress, Event event) {
        //Locate the workflow for the machine
        Flow flow = machineToFlowMapping.get(hostAddress);
        if(flow != null){
            flow.enqueue(event);
            flow.updateStatistics(hostAddress, event);

        } else {
            logger.warning(String.format(" No flow mapped for the machine %s. The event %s could not be dispatched and is being discarded.", hostAddress, event));
        }
    }

    @PreDestroy
    public void initiateShutDown() {
        this.runIndicator = false;
        System.out.println("Initiated shutdown.....");

        logger.info("Initiated shutdown.....");
    }

    public void shutDown(){
        System.out.println("Stopped main loop. Shutting down services......");

        logger.info("Stopped main loop. Shutting down services.");
        scheduledExecutorService.shutdown();
        taskExecutorService.shutdown();
        AdminAdapter.shutDown();


    }
}
