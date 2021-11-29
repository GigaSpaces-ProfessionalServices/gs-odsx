package com.gigaspaces.odsx.noderebalancer.admin.action;

import com.gigaspaces.odsx.noderebalancer.action.BaseAction;
import com.gigaspaces.odsx.noderebalancer.action.Status;
import com.gigaspaces.odsx.noderebalancer.admin.AdminAdapter;
import com.gigaspaces.odsx.noderebalancer.model.Context;
import org.openspaces.admin.gsc.GridServiceContainer;
import org.openspaces.admin.machine.Machine;
import org.openspaces.admin.machine.Machines;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;

public class DeleteContainerAction extends BaseAction {

    private String targetMachineCollectionKey;
    private String targetContainerMarkerKey;

    public DeleteContainerAction(Context context){
        super(context, Type.TASK);
    }

    @Override
    public Status callInternal() throws Exception {
        logger.info("Running DeleteAction");
        if(targetMachineCollectionKey == null || targetMachineCollectionKey.length() == 0){
            targetMachineCollectionKey = AdminAdapter.AdminContextId.RELOCATED_CONTAINERS_TARGET_HOSTS.label;
        }

        if( targetContainerMarkerKey == null || targetContainerMarkerKey.length() == 0){
            targetContainerMarkerKey = AdminAdapter.AdminContextId.NO_CONTAINER_MARKER.label;
        }

        Machines machines = AdminAdapter.getAdmin().getMachines();

        if(AdminAdapter.AdminContextId.SELF_HOST.label.equals(targetMachineCollectionKey)){
            String serverIpAddress = getFlowContext().getSetServerConfiguration().getIpAddress();
            Machine machine = machines.getMachineByHostAddress(serverIpAddress);
            if(machine == null){
                logger.warning("Could not find the self-machine to delete containers from " + serverIpAddress);
                return Status.FAILURE;
            }else {
                Set<String> zones = getFlowContext().getSetServerConfiguration().getZones();
                deleteContainersByZone(machine, zones);
                return  Status.SUCCESS;
            }
        }

        Object machineInfo  =  getFlowContext().getValue(targetMachineCollectionKey);
        Map<String, List<String>> targetMachineMap;
        if(! (machineInfo instanceof Map)){
            logger.warning(" Did not find collection of hosts to delete containers from , found : " + machineInfo);
            return  Status.FAILURE;
        }else {
            targetMachineMap  = (Map<String, List<String>>) machineInfo;
        }
        logger.info("Beginning to delete the containers : " + targetMachineMap );
        logger.info("Will iterate over the machine collection:   " + machines.getMachines() );

        Set<String> targetMachines = targetMachineMap.keySet();
        for(Machine machine : machines){
            if( targetMachines.contains( machine.getHostAddress())){
                List<String> containerIds = targetMachineMap.get(machine.getHostAddress());
                deleteContainersById(machine, containerIds);
            }
        }

        return Status.SUCCESS;
    }

    //TODO: Combine the two deleteContainer methods using a predicate lambda ?
    private void deleteContainersByZone(Machine machine, Set<String> zones) {
        logger.info(String.format(" Deleting containers on machine : %s , zones : %s",  machine.getHostAddress(), zones));
        GridServiceContainer[] containers = machine.getGridServiceContainers().getContainers();
        if (containers != null && containers.length > 0){
            for (GridServiceContainer container: containers){
                //Delete only the containers we created
                if(container.getExactZones().getZones().containsAll(zones) ){
                    container.kill();
                    logger.info("Deleted container with id : " + container.getId());
                }
            }
        }
    }

    private void deleteContainersById(Machine machine, List<String> containerIds) {
        logger.info(String.format(" Deleting containers on machine : %s , containers : %s",  machine.getHostAddress(), containerIds));
        GridServiceContainer[] containers = machine.getGridServiceContainers().getContainers();
        // If yes, remove them
        if (containers != null && containers.length > 0){
            for (GridServiceContainer container: containers){
                //Delete only the containers we created
                if(containerIds.contains(container.getId())){
                    container.kill();
                    logger.info("Deleted container with id : " + container.getId());
                }
            }
        }
    }

    public void setTargetMachineCollectionKey(String targetMachineCollectionKey) {
        this.targetMachineCollectionKey = targetMachineCollectionKey;
    }

    public void setTargetContainerMarker(String targetContainerMarkerKey) {
        this.targetContainerMarkerKey = targetContainerMarkerKey;
    }

}
