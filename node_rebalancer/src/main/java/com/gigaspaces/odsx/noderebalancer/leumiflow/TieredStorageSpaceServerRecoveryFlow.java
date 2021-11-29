package com.gigaspaces.odsx.noderebalancer.leumiflow;

import com.gigaspaces.odsx.noderebalancer.action.ConditionalTransitionAction;
import com.gigaspaces.odsx.noderebalancer.action.TimerAction;
import com.gigaspaces.odsx.noderebalancer.action.TransitionAction;
import com.gigaspaces.odsx.noderebalancer.admin.AdminAdapter;
import com.gigaspaces.odsx.noderebalancer.admin.action.*;
import com.gigaspaces.odsx.noderebalancer.event.EventDescrirptor;
import com.gigaspaces.odsx.noderebalancer.model.Flow;
import com.gigaspaces.odsx.noderebalancer.model.State;
import com.gigaspaces.odsx.noderebalancer.model.Trigger;

import java.util.Map;

public class TieredStorageSpaceServerRecoveryFlow  extends BaseRecoveryFlow {


    private final String serverIpAddress;

    public enum LocalState {
        INITIAL("Initial"),
        SERVER_DOWN_GRACE_PERIOD("ServerDownGracePeriod"),
        SERVER_DOWN("ServerDown"),
        SERVER_UP("ServerUp"),
        CONTAINER_CHECK("ContainerCheck"),
        CONTAINER_CREATE("ContainerCreate"),
        INSTANCE_REBALANCE("InstanceRebalance"),
        END("End");
        public final String label;
        private LocalState(String label){
            this.label = label;
        }
    };

    public TieredStorageSpaceServerRecoveryFlow(String name, String serverIpAddress) {
      super(name);
      this.serverIpAddress = serverIpAddress;
      getContext().setValue(AdminAdapter.AdminContextId.SELF_HOST.label, serverIpAddress);
    }

    public static TieredStorageSpaceServerRecoveryFlow build(String name, String serverIpAddress, Map<String, String> parameters){
        TieredStorageSpaceServerRecoveryFlow flow = new TieredStorageSpaceServerRecoveryFlow(name, serverIpAddress);
        flow.setParameters(parameters);
        State initialState = new State(LocalState.INITIAL.label);
        Trigger containerCreatedTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.ADMIN, AdminAdapter.EventCode.CONTAINER_ADDED.code));
        SaveContainerConfigurationAction saveContainerConfigurationAction = new SaveContainerConfigurationAction(flow.getContext());
        containerCreatedTrigger.addAction(saveContainerConfigurationAction);
        initialState.addTrigger(containerCreatedTrigger);
        Trigger machineRemovedTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.ADMIN, AdminAdapter.EventCode.MACHINE_REMOVED.code));
        TransitionAction transitionAction = new TransitionAction(flow.getContext(), LocalState.SERVER_DOWN_GRACE_PERIOD.label);
        machineRemovedTrigger.addAction(transitionAction);
        initialState.addTrigger(machineRemovedTrigger);
        flow.addState(initialState);
        flow.setInitialState(initialState);

        /**
         * This state is implementing the grace period / stability check - if the machine comes back during the
         * timer interval, we are back to business and go back to initial state. after container check. Otherwise, proceed to Server Down State.
         */
        State serverDownGracePeriodState = new State(LocalState.SERVER_DOWN_GRACE_PERIOD.label);
        Trigger enteringServerDownTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL, EventCode.ENTERING_STATE.code));
        //When timer is triggered after the specified ms and the server is not UP, we will take the relocation action.
        TimerAction timerAction = new TimerAction(flow.getContext(), flow.getLongParameter("waitIntervalAfterServerDown", 45*1000L));
        enteringServerDownTrigger.addAction(timerAction);
        serverDownGracePeriodState.addTrigger(enteringServerDownTrigger);
        //And if server is back up, we return to the initial state.
        Trigger serverUpTrigger = new Trigger(new EventDescrirptor( EventDescrirptor.EventSpace.ADMIN, AdminAdapter.EventCode.MACHINE_ADDED.code));
        TransitionAction transitionToContainerCheckStateAction = new TransitionAction(flow.getContext(), LocalState.CONTAINER_CHECK.label);
        serverUpTrigger.addAction(transitionToContainerCheckStateAction);
        serverDownGracePeriodState.addTrigger(serverUpTrigger);
        Trigger timerTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL, EventCode.ASYNC_TIMER_COMPLETED.code));
        timerTrigger.addAction(new TransitionAction(flow.getContext(), LocalState.SERVER_DOWN.label));
        serverDownGracePeriodState.addTrigger(timerTrigger);
        flow.addState(serverDownGracePeriodState);

        /** Now that we know the server is down,
         * Alert and wait for it to be up..
         *
         */
        State serverDownState = new State(LocalState.SERVER_DOWN.label);
        //And if server is back up, we return to the initial state.
        serverUpTrigger = new Trigger(new EventDescrirptor( EventDescrirptor.EventSpace.ADMIN, AdminAdapter.EventCode.MACHINE_ADDED.code));
        transitionToContainerCheckStateAction = new TransitionAction(flow.getContext(), LocalState.CONTAINER_CHECK.label);
        serverUpTrigger.addAction(transitionToContainerCheckStateAction);
        serverDownState.addTrigger(serverUpTrigger);
        flow.addState(serverDownState);

        /** Server is up, we check for containers now.
         *
         */
        State checkContainerState = new State(LocalState.CONTAINER_CHECK.label);
        Trigger enteringContainerCheckStateTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL, EventCode.ENTERING_STATE.code));
        CheckContainerAction containerCheckAction = new CheckContainerAction(flow.getContext());
        containerCheckAction.setContainerCountKey(CheckContainerAction.CONTAINER_COUNT_KEY);
        enteringContainerCheckStateTrigger.addAction(containerCheckAction);
        //If container are fine, we move to initial state, otherwise create containers
        String conditionExpression = " #this.getValue( \"ContainerCountKey\" ) > 0 ";
        ConditionalTransitionAction conditionalTransitionAction = new ConditionalTransitionAction(flow.getContext(), conditionExpression, LocalState.INSTANCE_REBALANCE.label);
        enteringContainerCheckStateTrigger.addAction(conditionalTransitionAction);
        transitionAction = new TransitionAction(flow.getContext(), LocalState.CONTAINER_CREATE.label);
        enteringContainerCheckStateTrigger.addAction(transitionAction);
        checkContainerState.addTrigger(enteringContainerCheckStateTrigger);
        flow.addState(checkContainerState);


        /**
         * Create missing containers and then back to INITIAL state.
         */
        State containerCreateState = new State(LocalState.CONTAINER_CREATE.label);
        Trigger enteringContainerCreateStateTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL, EventCode.ENTERING_STATE.code));
        CreateContainerAction createContainerAction = new CreateContainerAction(flow.getContext());
        createContainerAction.setTargetMachineCollectionKey(AdminAdapter.AdminContextId.SELF_HOST.label);
        enteringContainerCreateStateTrigger.addAction(createContainerAction);
        transitionAction = new TransitionAction(flow.getContext(), LocalState.INSTANCE_REBALANCE.label);
        enteringContainerCreateStateTrigger.addAction(transitionAction);
        containerCreateState.addTrigger(enteringContainerCreateStateTrigger);
        flow.addState(containerCreateState);


        /**
         * Rebalance the instances (f they are all backups)
         */
        State instanceRebalanceState = new State(LocalState.INSTANCE_REBALANCE.label);
        Trigger instanceRebalanceStateTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL, EventCode.ENTERING_STATE.code));
        instanceRebalanceState.addTrigger(instanceRebalanceStateTrigger);
        RebalanceAction rebalanceAction = new RebalanceAction(flow.getContext());
        rebalanceAction.setTargetMachineCollectionKey(AdminAdapter.AdminContextId.SELF_HOST.label);
        instanceRebalanceStateTrigger.addAction(rebalanceAction);
        //TODO: Do we clean-up context information at this point ? If not then when?
        transitionAction = new TransitionAction(flow.getContext(), LocalState.INITIAL.label);
        instanceRebalanceStateTrigger.addAction(transitionAction);
        flow.addState(instanceRebalanceState);

        return  flow;
    }
}
