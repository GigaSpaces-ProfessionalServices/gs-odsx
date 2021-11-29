package com.gigaspaces.odsx.noderebalancer.admin.action;

import com.gigaspaces.odsx.noderebalancer.action.BaseAction;
import com.gigaspaces.odsx.noderebalancer.action.Status;
import com.gigaspaces.odsx.noderebalancer.admin.AdminAdapter;
import com.gigaspaces.odsx.noderebalancer.admin.model.ContainerConfiguration;
import com.gigaspaces.odsx.noderebalancer.model.Context;
import com.gigaspaces.odsx.noderebalancer.policy.ServerConfiguration;
import org.openspaces.admin.Admin;
import org.openspaces.admin.gsc.GridServiceContainer;
import org.openspaces.admin.machine.Machine;


import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;

public class CheckContainerAction extends BaseAction {

    public static final String CONTAINER_COUNT_KEY = "ContainerCountKey";
    private  String containerCountKey ;

    /**
     * Checks if machine has enough number of containers.
     *
     * There should be some delay in between a server being added and this action being called, so that the adming
     * instance is aware of all containers available with the machine.
     * @param context
     */
    public CheckContainerAction(Context context) {
        super(context, Type.TASK);
    }

    public void setContainerCountKey(String containerCountKey){
        this.containerCountKey = containerCountKey;
    }


    @Override
    public Status callInternal() throws Exception {
        // Get container count for this machine
        logger.info("Executing the action :" + this.getClass().getName());

        if(containerCountKey == null){
            containerCountKey = CONTAINER_COUNT_KEY;
        }

        ServerConfiguration serverConfiguration = getFlowContext().getSetServerConfiguration();

        Admin admin = AdminAdapter.getAdmin();
        Machine targetMachine = admin.getMachines().waitFor(serverConfiguration.getIpAddress(), 5, TimeUnit.SECONDS);

        if(targetMachine == null){
            logger.severe(" The machine with the ip address not found for counting containers : " + serverConfiguration.getIpAddress());
            //TODO: Confirm any additional alert beyond the logging needed
            return  Status.FAILURE;
        }
        //ToDo: Implement wait using exponential where wait time increased if attempt was unsuccessful and check for events in between re tries
        targetMachine.getGridServiceContainers().waitFor(getFlowContext().getContainerCount(), getFlowContext().getLongParameter("waitIntervalForContainerCheckForAdminApi",30*1000L), TimeUnit.MILLISECONDS);
        int containerCount = 0;
        for (GridServiceContainer container : targetMachine.getGridServiceContainers()){
            containerCount++;
        }

        logger.info(" Total containers counted : " + containerCount);
        getFlowContext().setValue(containerCountKey, containerCount);

        return Status.SUCCESS;
    }
}
