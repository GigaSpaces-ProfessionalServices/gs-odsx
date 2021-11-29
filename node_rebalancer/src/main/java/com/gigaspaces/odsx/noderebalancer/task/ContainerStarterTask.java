package com.gigaspaces.odsx.noderebalancer.task;

import com.gigaspaces.odsx.noderebalancer.CurrentStateHelper;
import com.gigaspaces.odsx.noderebalancer.admin.model.ContainerConfiguration;
import org.openspaces.admin.gsa.GridServiceContainerOptions;
import org.openspaces.admin.machine.Machine;

import java.util.ArrayList;
import java.util.Map;
import java.util.concurrent.Callable;
import java.util.logging.Logger;

public class ContainerStarterTask<Integer> implements Callable<java.lang.Integer> {

    ArrayList<ContainerConfiguration>  containers;
    CurrentStateHelper currentStateHelper;

    Logger logger = Logger.getLogger(ContainerStarterTask.class.getName());

    public ContainerStarterTask(CurrentStateHelper currentStateHelper, ArrayList<ContainerConfiguration> containers
    ){
        this.containers = containers;
        this.currentStateHelper = currentStateHelper;
    }


    @Override
    public java.lang.Integer call() throws Exception {
        //TODO: remove this task from scheduled tasks collection

        logger.info(" Running container creation for containers : " + containers);


        // Get Machines
        // Check Machine Capacities
        // Determine machines to run container on
        //TODO: Is the single machine for all containers - or for-each containers find machine again - or get all candidate machines in one go
        Machine machine = currentStateHelper.geMachineWithMostFreeMemory();

        if(machine == null){
            logger.warning("Did not get available machine to relocate containers. Task will exit.");
            java.lang.Integer result = -1;
            return result;
        }
        // Get agent from the machines
        // Launch container
        for( ContainerConfiguration container: containers){
            GridServiceContainerOptions.Builder builder  = new  GridServiceContainerOptions.Builder();
            builder.vmOptions(container.options.vmArguments);
            GridServiceContainerOptions options = builder.build();
            for( Map.Entry<String, String> entry : container.options.environmentVariables.entrySet()){
                options.environmentVariable(entry.getKey(), entry.getValue());
            }
            String zonesVmInputArgument = "com.gs.zones=";
            for(String zone: container.zones){
                zonesVmInputArgument +=  zone + ",";
            }
            options.vmInputArgument(zonesVmInputArgument.substring(0,zonesVmInputArgument.length()-1) );

            //TODO: We need to get UID (or some other distinct referece ) of this newly created
            // container, and pass it on to the toBeRebalanced collection, so that later on,
            // when it is time, this container can be appropriately dealt with (e.g. demote or stop)
            machine.getGridServiceAgent().startGridService(options);


            //TODO: For rebalancing, we want to -
            //      A. watch for the original machine to come back -
            //      B. If the original machine comes back:
            //          1. Start containers on the original machine
            //          2. Stop containers on the machines where they were created.
            // Therefore,
            // - store  rebalancing information to support lookup using the original machine
            // - On Machine added event, track if this is one of the machine we are tracking
            //      - if so, trigger rebalance
            //          - Boundary Scenario -   What if the machine that we relocated to has gone down.
            currentStateHelper.addContainerForReBalancing( machine.getHostAddress(), machine.getHostName(), containers);
        }
        int result = 0;
        return  result;
    }
}
