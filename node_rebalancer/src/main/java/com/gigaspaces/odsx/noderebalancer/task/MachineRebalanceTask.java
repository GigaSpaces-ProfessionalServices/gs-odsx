package com.gigaspaces.odsx.noderebalancer.task;

import com.gigaspaces.odsx.noderebalancer.CurrentStateHelper;
import com.gigaspaces.odsx.noderebalancer.admin.model.ContainerConfiguration;
import com.gigaspaces.odsx.noderebalancer.admin.model.ToBeRebalancedResource;
import org.openspaces.admin.gsa.GridServiceAgent;
import org.openspaces.admin.gsa.GridServiceContainerOptions;
import org.openspaces.admin.gsc.GridServiceContainer;
import org.openspaces.admin.machine.Machine;
import org.openspaces.admin.pu.ProcessingUnitInstance;

import java.util.ArrayList;
import java.util.Map;
import java.util.concurrent.Callable;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;

public class MachineRebalanceTask<Integer> implements Callable<java.lang.Integer> {

    ToBeRebalancedResource toBeRebalancedResource;
    CurrentStateHelper currentStateHelper;

    Logger logger = Logger.getLogger(MachineRebalanceTask.class.getName());

    public MachineRebalanceTask(CurrentStateHelper currentStateHelper, ToBeRebalancedResource toBeRebalancedResource){
        this.currentStateHelper = currentStateHelper;
        this.toBeRebalancedResource = toBeRebalancedResource;
    }

    @Override
    public java.lang.Integer call() throws Exception {
        //TODO: remove this task from scheduled tasks collection

        ArrayList<Future<?>> demotionCalls = new ArrayList<Future<?>>();
        ArrayList<GridServiceContainer> oldContainers = new ArrayList<GridServiceContainer>();

        logger.info(" Checking machine rebalancing  for machine : " + toBeRebalancedResource.containers.get(0).originalHostAddress);

        // Check if the machine has containers
        String hostIP = toBeRebalancedResource.containers.get(0).originalHostAddress;
        Machine machine = currentStateHelper.getMachine(hostIP);

        //TODO: Did we find machine ? What if not?
        GridServiceAgent gridServiceAgent = machine.getGridServiceAgent();
        if( machine == null){
            logger.warning(" Attempting to rebalance the machine, but could not find the machine. Canceling the teask. Machine IP : " + hostIP);
            return  -1;
        }
        GridServiceContainer [] containers = machine.getGridServiceContainers().getContainers();
        // If yes, remove them
        //TODO: All containers or only specific ones?
        if (containers != null && containers.length > 0){
            for (GridServiceContainer container: containers){
                container.kill();
            }
        }
        // Create fresh containers, Demote the newly created containers
        for(ContainerConfiguration containerInfo: toBeRebalancedResource.containers){
            //gridServiceAgent.startGridService();

            GridServiceContainerOptions.Builder builder  = new  GridServiceContainerOptions.Builder();
            builder.vmOptions(containerInfo.options.vmArguments);
            GridServiceContainerOptions options = builder.build();
            for( Map.Entry<String, String> entry : containerInfo.options.environmentVariables.entrySet()){
                options.environmentVariable(entry.getKey(), entry.getValue());
            }
            String zonesVmInputArgument = "com.gs.zones=";
            for(String zone: containerInfo.zones){
                zonesVmInputArgument +=  zone + ",";
            }
            options.vmInputArgument(zonesVmInputArgument.substring(0,zonesVmInputArgument.length()-1) );

            //TODO: We need to get UID (or some other distinct referece ) of this newly created
            // container so that we can refer to it later if nend be
            machine.getGridServiceAgent().startGridService(options);

            //TODO: Check if we are storing uid of newly created container or old one ?
            // If old one, then how to identify the container ?
            Machine targetMachine = currentStateHelper.getMachine(toBeRebalancedResource.targetHostAddress);

            GridServiceContainer oldContainer = targetMachine.getGridServiceContainers().getContainerByUID(containerInfo.uid);
            // Demote the previously created container

            if(oldContainer != null){
               ProcessingUnitInstance instances[] = oldContainer.getProcessingUnitInstances();
               //TODO: which ones to demote ? Currently demoting all of them
                for(ProcessingUnitInstance instance : instances){
                    //TODO: Do we need to retain this ? Why?
                    Future<?> future = instance.getSpaceInstance().demote(15, TimeUnit.SECONDS) ;
                    demotionCalls.add(future);
                    oldContainers.add(oldContainer);
                }
            }
        }
        // Wait for some time and then kill the demoted (ex newly created) containers
        int index = 0;
        for ( Future<?> future : demotionCalls){
            future.get();
            GridServiceContainer container = oldContainers.get(index++);
            container.kill();
        }

        int result = 0;
        return  result;
    }
}
