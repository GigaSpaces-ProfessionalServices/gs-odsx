package com.gigaspaces.odsx.noderebalancer.admin.action;

import com.gigaspaces.odsx.noderebalancer.action.BaseAction;
import com.gigaspaces.odsx.noderebalancer.action.Status;
import com.gigaspaces.odsx.noderebalancer.admin.AdminAdapter;
import com.gigaspaces.odsx.noderebalancer.model.Context;
import org.openspaces.admin.gsc.GridServiceContainer;
import org.openspaces.admin.machine.Machine;
import org.openspaces.admin.pu.ProcessingUnitInstance;
import org.openspaces.admin.space.SpaceInstance;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Demote space instances on a one or more machine.
 *
 */
public class DemoteContainerAction extends BaseAction {

    private String targetMachineCollectionKey;

    //TODO: Demotion operation is incorrect. It needs to identify correct target machine and exact sequence is to be clarified.

    public DemoteContainerAction(Context context){
        super(context,Type.TASK);
    }

    @Override
    public Status callInternal() throws Exception {
        logger.info("Running the DemoteContainerAction action.");

        if(targetMachineCollectionKey == null || targetMachineCollectionKey.length() == 0){
            targetMachineCollectionKey = AdminAdapter.AdminContextId.RELOCATED_CONTAINERS_TARGET_HOSTS.label;
        }

        // Get Machines to demote containers on
        Object machineInfo = getFlowContext().getValue(targetMachineCollectionKey);

        Map<String, List<String>> targetMachineMap;
        if(! (machineInfo instanceof Map)){
            logger.warning(" Did not find collection of hosts to demote containers from , found : " + machineInfo);
            return  Status.FAILURE;
        }else {
            targetMachineMap  = (Map<String, List<String>>) machineInfo;
        }
        Set<String> targetMachines = targetMachineMap.keySet();

        if (targetMachines.size() == 0) {
            logger.warning("Did not get  machines to demote containers. Task will exit.");
            return Status.FAILURE;
        }

        Machine[] machines = AdminAdapter.getAdmin().getMachines().getMachines();
        int totalDemotedContainers = 0;
        for(Machine machine : machines){
            int demotedContainerCount = 0;
            if( targetMachines.contains( machine.getHostAddress())){
                List<String> containerIds = targetMachineMap.get(machine.getHostAddress());
                demotedContainerCount = demoteContainers(machine, containerIds);
                totalDemotedContainers += demotedContainerCount;
            }
        }
        logger.info("Completed demote container operation. Total demoted containers: " + totalDemotedContainers);
        return Status.SUCCESS;
    }

    private int demoteContainers(Machine machine,  List<String> containerIds) {
        int demotedContainerCount;
        int containerCount;
        logger.log(Level.INFO, "Got machine with containers to demote - {0}. ", machine.getHostAddress());
        GridServiceContainer[] containers = machine.getGridServiceContainers().getContainers();
        containerCount = containers.length;
        demotedContainerCount = 0;
        // If yes, demote them
        if (containers != null && containers.length > 0){
            for (GridServiceContainer container: containers){
                //Demote only the containers we created
                if(containerIds.contains(container.getId())){
                    demoteSpaces(container);
                    demotedContainerCount++;
                }
            }
        }
        logger.log(Level.INFO, "On machine {0}, of total {1} containers, demoted {2} ." , new Object[]{ machine.getHostAddress(), containerCount, demotedContainerCount} ) ;
        return demotedContainerCount;
    }

    private void demoteSpaces(GridServiceContainer container) {
        ProcessingUnitInstance instances[] = container.getProcessingUnitInstances();
        for(ProcessingUnitInstance instance : instances){
            //TODO: What is the MaxSuspect time value ? Shouldn't' it come from config?
            SpaceInstance spaceInstance = instance.getSpaceInstance();
            SpaceInstance primaryInstance = spaceInstance.getPartition().getPrimary();
            if(spaceInstance.equals(primaryInstance)){
                Future<?> future = spaceInstance.demote(5, TimeUnit.SECONDS) ;
                logger.info("Demoting primary instance " + spaceInstance);
            }
            //TODO: Handle exception
        }
    }


    public void setTargetMachineCollectionKey(String targetMachineCollectionKey) {
        this.targetMachineCollectionKey = targetMachineCollectionKey;
    }


}
