package com.gigaspaces.odsx.noderebalancer.admin.action;

import com.gigaspaces.odsx.noderebalancer.util.MachineFinder;
import com.gigaspaces.odsx.noderebalancer.action.BaseAction;
import com.gigaspaces.odsx.noderebalancer.action.Status;
import com.gigaspaces.odsx.noderebalancer.admin.AdminAdapter;
import com.gigaspaces.odsx.noderebalancer.admin.model.ContainerConfiguration;
import com.gigaspaces.odsx.noderebalancer.model.Context;
import com.gigaspaces.odsx.noderebalancer.model.Pair;
import com.gigaspaces.odsx.noderebalancer.policy.ServerConfiguration;
import org.openspaces.admin.Admin;
import org.openspaces.admin.gsa.GridServiceContainerOptions;
import org.openspaces.admin.gsc.GridServiceContainer;
import org.openspaces.admin.machine.Machine;

import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

public class CreateContainerAction extends BaseAction {

    private String targetMachineCollectionKey;
    public static final String RECOVERY_FLOW_CREATED_CONTAINER_MARKER = "ORIGINAL_HOST_IP";

    public CreateContainerAction(Context context) {
        super(context, Type.TASK);
    }

    Logger logger = Logger.getLogger(CreateContainerAction.class.getName());

    @Override
    public Status callInternal() throws Exception {
        logger.info("Creating containers originally  of the machine - " + getFlowContext().getSetServerConfiguration().getIpAddress());

        //TODO: Instead of being permissive and assuming default, if configuration is not correct,
        // Please consider failing fast, here and now. Bitter but better feedback :)
        if(targetMachineCollectionKey == null || targetMachineCollectionKey.length() == 0){
            targetMachineCollectionKey = AdminAdapter.AdminContextId.RELOCATED_CONTAINERS_TARGET_HOSTS.label;
        }
        ServerConfiguration serverConfiguration = getFlowContext().getSetServerConfiguration();

        String targetContainerMarkerValue = "";
        int containersCreated = 0;
        Admin admin = AdminAdapter.getAdmin();
        //TODO: filter machines where containers are not to be created e.g, Manager
        //TODO: Instead, get the space server machines from configuration ?
        admin.getMachines().waitFor(1);
        Machine machines[] = admin.getMachines().getMachines();
        LinkedList<String> machinesList = new LinkedList<>();

        Machine targetMachine = null;

        /*
         * If the target machine where the containers are to be created is the original host
         * for which the workflow is running, then get from Admin reference to that machine.
         * (Instead of searching for machine with more free memory)
         */
        if(targetMachineCollectionKey.equals(AdminAdapter.AdminContextId.SELF_HOST.label)) {
            //Map ip address string to Admin machine reference
            targetMachine = getAdminMachineFromIpAddress(serverConfiguration.getIpAddress(), machines);
            if( targetContainerMarkerValue == null){
                logger.severe(" Could not find SELF_HOST machine for this workflow, create container will fail.");
                return Status.FAILURE;
            }
            targetContainerMarkerValue = "";
        } else {
            targetContainerMarkerValue = serverConfiguration.getIpAddress();
        }

        Map<String, List<String>> createdContainersMap = new HashMap<>();
        for (String zone : serverConfiguration.getZones()){
            int containerCount = serverConfiguration.getZoneContainerCount(zone);
            if(getFlowContext().getValue(zone) == null || !(getFlowContext().getValue(zone) instanceof ContainerConfiguration)){
                logger.warning(String.format("Did not get expected value of container configuration for zone %s ,value is %s", zone, getFlowContext().getValue(zone)));
            }
            else{
                ContainerConfiguration containerConfiguration = ( ContainerConfiguration) getFlowContext().getValue(zone);
                logger.info(" Running container creation for container : " + containerConfiguration);
                boolean abortedContainerCreation = false;
                for(int i = 0; i < containerCount; i++){
                    Machine machine;
                    if(targetMachine == null){
                        //Check if the server is up
                        if (getFlowContext().isServerUp()){
                            logger.info(String.format("Server is up, stopping the container creation process after creation of %s containers.", containersCreated));
                            break;
                        }
                        machine = findMachine(machines, serverConfiguration.getServerGroup());
                        if(machine == null){
                            logger.warning("Machine not available when trying to create container for : " + containerConfiguration);
                            continue;
                        }
                        machinesList.add(machine.getHostAddress());

                    }else {
                        machine = targetMachine;
                    }
                    GridServiceContainer container = createContainer(targetContainerMarkerValue, containerConfiguration, machine);
                    List<String> containerIds;
                    String containerId = container.getId();
                    containerIds = createdContainersMap.get(machine.getHostAddress());
                    if(containerIds == null ){
                        containerIds = new LinkedList<>();
                        createdContainersMap.put(machine.getHostAddress(), containerIds);
                    }
                    containerIds.add(containerId);
                    containersCreated++;
                }
                if( ! targetMachineCollectionKey.equals(AdminAdapter.AdminContextId.SELF_HOST.label) ){
                    // Track the machines where were are storing information
                    getFlowContext().setValue(targetMachineCollectionKey, createdContainersMap);
                    logger.log(Level.INFO, " Stored container and host information context key {0} , the map is {1}",
                            new Object [] {
                                    targetMachineCollectionKey, createdContainersMap
                            }
                    );
                }

            }

        }

        logger.info(" Total containers created : " + containersCreated);
        return Status.SUCCESS;
    }

    private Machine getAdminMachineFromIpAddress(String  ipAddress, Machine[] machines) {
        Machine targetMachine = null;
        for (Machine machine : machines) {
            if (ipAddress.equals(machine.getHostAddress())) {
                targetMachine = machine;
                break;
            }
        }
        return targetMachine;
    }

    private Machine findMachine(Machine[] machines, List<String> serverGroup) {
        Machine machine;
        //Find best machine to add this
        //container.zones
        //TODO: Pass zone and only select machines supporting the provided zone
        Pair<Machine, Long> machineInfo = new MachineFinder().findMachineWithRAM(machines, serverGroup);
        machine = machineInfo.getFirst();
        logger.log(Level.INFO, "Found machined for creating container {0}.", (machine == null ? "NOT FOUND" : machine.getHostAddress()));
        return machine;
    }

    private GridServiceContainer createContainer(String targetContainerMarkerValue, ContainerConfiguration containerConfiguration, Machine machine) {
       /*
        GridServiceContainerOptions.Builder builder  = new  GridServiceContainerOptions.Builder();
        builder.vmOptions(containerConfiguration.options.vmArguments);
        for(String zone: containerConfiguration.zones){
            builder.zone(zone);
        }
        */

        GridServiceContainerOptions options = new GridServiceContainerOptions();

        for( String vmArgument : containerConfiguration.options.vmArguments){
            options.vmInputArgument(vmArgument);
        }

        String zonesVmInputArgument = "com.gs.zones=";
        for(String zone: containerConfiguration.zones){
            zonesVmInputArgument +=  zone + ",";
        }
        options.vmInputArgument(zonesVmInputArgument.substring(0,zonesVmInputArgument.length()-1));

        for( Map.Entry<String, String> entry : containerConfiguration.options.environmentVariables.entrySet()){
            options.environmentVariable(entry.getKey(), entry.getValue());
        }
        if( targetContainerMarkerValue != null && targetContainerMarkerValue.length() > 0){
            options.environmentVariable(RECOVERY_FLOW_CREATED_CONTAINER_MARKER, targetContainerMarkerValue);
        }

        options.useScript();
        logger.info(" Creating container with options : " + toString(options));
        //TODO: Should we time out instead indefinately waiting ?
        GridServiceContainer containerCreated = machine.getGridServiceAgent().startGridServiceAndWait(options);
        return containerCreated;
    }

    private String toString(GridServiceContainerOptions options) {
        return "  Env. Variables: { " + options.getOptions().getEnvironmentVariables()
                + "} , VM arguments { " + options.getOptions().getVmInputArguments() + "}";
    }

    public void setTargetMachineCollectionKey(String targetMachineCollectionKey) {
        this.targetMachineCollectionKey = targetMachineCollectionKey;
    }


}
