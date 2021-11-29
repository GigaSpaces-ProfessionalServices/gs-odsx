package com.gigaspaces.odsx.noderebalancer.leumiflow;

import com.gigaspaces.odsx.noderebalancer.action.*;
import com.gigaspaces.odsx.noderebalancer.admin.AdminAdapter;
import com.gigaspaces.odsx.noderebalancer.admin.action.*;
import com.gigaspaces.odsx.noderebalancer.event.EventDescrirptor;
import com.gigaspaces.odsx.noderebalancer.model.Flow;
import com.gigaspaces.odsx.noderebalancer.model.State;
import com.gigaspaces.odsx.noderebalancer.model.Trigger;

import java.util.Map;

public class SpaceServerRecoveryFlow  extends BaseRecoveryFlow {


    private final String serverIpAddress;

    public enum LocalState {
        INITIAL("Initial"),
        STABLE("Stable"),
        SERVER_DOWN("ServerDown"),
        CONTAINER_CHECK("ContainerCheck"),
        RELOCATE_CONTAINER("RelocateContainer"),
        CONTAINER_RELOCATED("ContainerRelocated"),
        SERVER_UP("ServerUp"),
        INSTANCE_REBALANCE("InstanceRebalance"),
        END("End");
        public final String label;
        private LocalState(String label){
            this.label = label;
        }
    };
    public SpaceServerRecoveryFlow(String name, String serverIpAddress) {
        super(name);
        this.serverIpAddress = serverIpAddress;
        getContext().setValue(AdminAdapter.AdminContextId.SELF_HOST.label, serverIpAddress);

        //TODO: Check construction of all this and super elements completed and initialized
    }

    public static SpaceServerRecoveryFlow build(String name, String serverIpAddress, Map<String, String> parameters){
        SpaceServerRecoveryFlow flow = new SpaceServerRecoveryFlow(name, serverIpAddress);
        flow.setParameters(parameters);

        /**
         * Initial state exists to provide some time for the Admin Client to stabilize and handle the
         * initial flood of events.
         */
        State initialState = new State(LocalState.INITIAL.label);
        Trigger enteringInitialStateTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL, EventCode.ENTERING_STATE.code));
        //Set up the timer to transition to next state (allows for initialization)
        TimerAction timerAction = new TimerAction(flow.getContext(), flow.getLongParameter("waitIntervalForInitialization", 3*60*1000L));
        enteringInitialStateTrigger.addAction(timerAction);
        initialState.addTrigger(enteringInitialStateTrigger);
        //Save container configuration
        Trigger containerCreatedTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.ADMIN, AdminAdapter.EventCode.CONTAINER_ADDED.code));
        SaveContainerConfigurationAction saveContainerConfigurationAction = new SaveContainerConfigurationAction(flow.getContext());
        containerCreatedTrigger.addAction(saveContainerConfigurationAction);
        initialState.addTrigger(containerCreatedTrigger);
        //On Timer, move to the stable state
        Trigger timerTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL, EventCode.ASYNC_TIMER_COMPLETED.code));
        timerTrigger.addAction(new TransitionAction(flow.getContext(), LocalState.STABLE.label));
        initialState.addTrigger(timerTrigger);

        flow.addState(initialState);
        flow.setInitialState(initialState);


        /** Stable State - we expect most of the time will be spent here.
         *
         */
        State stableState = new State(LocalState.STABLE.label);
        // This  is the stable state. After handling a downtime, the flow returns here. However,
        // if the server was down again while we were on the way to this state, we do not want to miss that and start the recovery again.
        Trigger enteringStableState = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL,EventCode.ENTERING_STATE.code));
        String conditionExpression = " #this.isServerUp() == false ";
        ConditionalTransitionAction conditionalTransitionAction = new ConditionalTransitionAction(flow.getContext(), conditionExpression, LocalState.SERVER_DOWN.label);
        enteringStableState.addAction(conditionalTransitionAction);
        stableState.addTrigger(enteringStableState);
        containerCreatedTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.ADMIN, AdminAdapter.EventCode.CONTAINER_ADDED.code));
        saveContainerConfigurationAction = new SaveContainerConfigurationAction(flow.getContext());
        containerCreatedTrigger.addAction(saveContainerConfigurationAction);
        stableState.addTrigger(containerCreatedTrigger);
        Trigger machineRemovedTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.ADMIN, AdminAdapter.EventCode.MACHINE_REMOVED.code));
        TransitionAction transitionAction = new TransitionAction(flow.getContext(),LocalState.SERVER_DOWN.label);
        machineRemovedTrigger.addAction(transitionAction);
        stableState.addTrigger(machineRemovedTrigger);
        flow.addState(stableState);


        /**
         * This state is implementing the grace period / stability check - if the machine comes back during the
         * timer interval, we are back to business and go back to stable state. Otherwise, proceed to recovery.
         */
        State serverDownState = new State(LocalState.SERVER_DOWN.label);
        Trigger enteringServerDownTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL, EventCode.ENTERING_STATE.code));
        //When timer is triggered after the specified ms and the server is not UP, we will take the relocation action.
        timerAction = new TimerAction(flow.getContext(), flow.getLongParameter("waitIntervalAfterServerDown", 45*1000L));
        enteringServerDownTrigger.addAction(timerAction);
        serverDownState.addTrigger(enteringServerDownTrigger);
        //And if server is back up, we check if containers are present, by moving to check container state.
        Trigger serverUpTrigger = new Trigger(new EventDescrirptor( EventDescrirptor.EventSpace.ADMIN, AdminAdapter.EventCode.MACHINE_ADDED.code));
        TransitionAction transitionToInitialStateAction = new TransitionAction(flow.getContext(),LocalState.CONTAINER_CHECK.label);
        serverUpTrigger.addAction(transitionToInitialStateAction);
        serverDownState.addTrigger(serverUpTrigger);
        //Otherwise, after elapsed time, we begin to relocate containers by moving to the Relocate Container State.
        timerTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL, EventCode.ASYNC_TIMER_COMPLETED.code));
        timerTrigger.addAction(new TransitionAction(flow.getContext(), LocalState.RELOCATE_CONTAINER.label));
        serverDownState.addTrigger(timerTrigger);
        flow.addState(serverDownState);

        /** This state acts as a branching point or fork.
         * If the server came back up during the grace period than this could be due to either
         *  (a) fast reboot or
         *  (b) network glitch.
         *  In case of (a), there will be no containers, so we will need to create them. In case (b), we
         *  can go back to the initial state, after rebalancing.
         *  In both the cases above, rebalancing might be needed as the containers will be all backup instances.
         */
        State checkContainerState = new State(LocalState.CONTAINER_CHECK.label);
        Trigger enteringCheckContainerStateTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL, EventCode.ENTERING_STATE.code));
        CheckContainerAction checkContainerAction = new CheckContainerAction(flow.getContext());
        checkContainerAction.setContainerCountKey(CheckContainerAction.CONTAINER_COUNT_KEY);
        enteringCheckContainerStateTrigger.addAction(checkContainerAction);
        //If container are fine, we move to initial state, otherwise create containers
        conditionExpression = " #this.getValue( \"ContainerCountKey\" ) > 0 ";
        conditionalTransitionAction = new ConditionalTransitionAction(flow.getContext(), conditionExpression, LocalState.INSTANCE_REBALANCE.label);
        enteringCheckContainerStateTrigger.addAction(conditionalTransitionAction);

        //If condition was false, the containers are not there and need to be created
        CreateContainerAction createContainerAction = new CreateContainerAction(flow.getContext());
        createContainerAction.setTargetMachineCollectionKey(AdminAdapter.AdminContextId.SELF_HOST.label);
        enteringCheckContainerStateTrigger.addAction(createContainerAction);
        //After creating containers, there should be some delay and then back to rebalance action
        enteringCheckContainerStateTrigger.addAction(new TransitionAction(flow.getContext(), LocalState.INSTANCE_REBALANCE.label));
        checkContainerState.addTrigger(enteringCheckContainerStateTrigger);
        flow.addState(checkContainerState);


        /** Now that we know the server is down, carry out action of container relocation here.
         *
         */
        State relocateContainerState = new State(LocalState.RELOCATE_CONTAINER.label);
        Trigger enteringRelocateContainerStateTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL, EventCode.ENTERING_STATE.code));
        createContainerAction = new CreateContainerAction(flow.getContext());
        createContainerAction.setTargetMachineCollectionKey(AdminAdapter.AdminContextId.RELOCATED_CONTAINERS_TARGET_HOSTS.label);
        enteringRelocateContainerStateTrigger.addAction(createContainerAction);
        conditionExpression = " #this.isServerUp() ";
        conditionalTransitionAction = new ConditionalTransitionAction(flow.getContext(), conditionExpression, LocalState.SERVER_UP.label);
        enteringCheckContainerStateTrigger.addAction(conditionalTransitionAction);
        transitionAction = new TransitionAction(flow.getContext(),LocalState.CONTAINER_RELOCATED.label);
        enteringRelocateContainerStateTrigger.addAction(transitionAction);
        relocateContainerState.addTrigger(enteringRelocateContainerStateTrigger);
        flow.addState(relocateContainerState);

        /**  In this state, we have recovery action performed while the original machine is unavailable.
         * Now, we watch if the original machine comes back and if yes,  move to reverse the recovery actions.
         */
        State containerRelocatedState = new State(LocalState.CONTAINER_RELOCATED.label);
        //On entering this state, check if the machine is already up (because we ignore server up event in the previous state
        Trigger enteringcontainerRelocatedState = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL,EventCode.ENTERING_STATE.code));
        conditionExpression = " #this.isServerUp() == true ";
        conditionalTransitionAction = new ConditionalTransitionAction(flow.getContext(), conditionExpression, LocalState.SERVER_UP.label);
        enteringcontainerRelocatedState.addAction(conditionalTransitionAction);
        containerRelocatedState.addTrigger(enteringcontainerRelocatedState);

        Trigger serverUpAgainTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.ADMIN, AdminAdapter.EventCode.MACHINE_ADDED.code));
        transitionAction = new TransitionAction(flow.getContext(), LocalState.SERVER_UP.label);
        serverUpAgainTrigger.addAction(transitionAction);
        containerRelocatedState.addTrigger(serverUpAgainTrigger);
        flow.addState(containerRelocatedState);

        /**
         * Post recovery action, the original machine has surfaced back so we have to reverse (or rollback) the recovery
         * actions and attempt to bring the original machie up to the speed.
         */
        State serverUpState = new State(LocalState.SERVER_UP.label);
        Trigger enteringServerUpStateTrigger = new Trigger(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL, EventCode.ENTERING_STATE.code));
        serverUpState.addTrigger(enteringServerUpStateTrigger);
        DelayAction delayAction = new DelayAction(flow.getLongParameter("waitIntervalForContainerCheckAfterServerUp", 25*1000L));
        enteringServerUpStateTrigger.addAction(delayAction);
        // If the machine which has returned, has any containers, they are stale and so are being deleted
        DeleteContainerAction deleteContainerAction = new DeleteContainerAction(flow.getContext());
        deleteContainerAction.setTargetMachineCollectionKey(AdminAdapter.AdminContextId.SELF_HOST.label);
        deleteContainerAction.setTargetContainerMarker(AdminAdapter.AdminContextId.NO_CONTAINER_MARKER.label); // Delete all
        enteringServerUpStateTrigger.addAction(deleteContainerAction);
        createContainerAction = new CreateContainerAction(flow.getContext());
        createContainerAction.setTargetMachineCollectionKey(AdminAdapter.AdminContextId.SELF_HOST.label);
        enteringServerUpStateTrigger.addAction(createContainerAction);
        DemoteContainerAction demoteContainerAction = new DemoteContainerAction(flow.getContext());
        demoteContainerAction.setTargetMachineCollectionKey(AdminAdapter.AdminContextId.RELOCATED_CONTAINERS_TARGET_HOSTS.label);
        enteringServerUpStateTrigger.addAction(demoteContainerAction);
        delayAction = new DelayAction( flow.getLongParameter("waitIntervalForDeletionAfterDemote",15*1000L));
        enteringServerUpStateTrigger.addAction(delayAction);
        deleteContainerAction = new DeleteContainerAction(flow.getContext());
        deleteContainerAction.setTargetMachineCollectionKey(AdminAdapter.AdminContextId.RELOCATED_CONTAINERS_TARGET_HOSTS.label);
        deleteContainerAction.setTargetContainerMarker(CreateContainerAction.RECOVERY_FLOW_CREATED_CONTAINER_MARKER);
        enteringServerUpStateTrigger.addAction(deleteContainerAction);
        delayAction = new DelayAction( flow.getLongParameter("waitIntervalForRebalance",90*1000L));
        enteringServerUpStateTrigger.addAction(delayAction);
        transitionAction = new TransitionAction(flow.getContext(),LocalState.INSTANCE_REBALANCE.label);
        enteringServerUpStateTrigger.addAction(transitionAction);
        flow.addState(serverUpState);

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
        transitionAction = new TransitionAction(flow.getContext(),LocalState.STABLE.label);
        instanceRebalanceStateTrigger.addAction(transitionAction);
        flow.addState(instanceRebalanceState);
        
        return  flow;
    }
}
