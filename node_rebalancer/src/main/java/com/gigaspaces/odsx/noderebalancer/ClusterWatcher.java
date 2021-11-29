package com.gigaspaces.odsx.noderebalancer;

import com.gigaspaces.odsx.noderebalancer.admin.model.ContainerConfiguration;
import com.gigaspaces.odsx.noderebalancer.task.ContainerStarterTask;
import com.gigaspaces.odsx.noderebalancer.model.Pair;
import com.gigaspaces.odsx.noderebalancer.admin.model.ContainerOptionsInfo;
import com.gigaspaces.odsx.noderebalancer.admin.model.ToBeRebalancedResource;
import com.gigaspaces.odsx.noderebalancer.task.MachineRebalanceTask;
import com.gigaspaces.odsx.noderebalancer.util.MachineFinder;
import org.openspaces.admin.Admin;
import org.openspaces.admin.AdminFactory;
import org.openspaces.admin.gsa.GridServiceAgent;
import org.openspaces.admin.gsa.GridServiceContainerOptions;
import org.openspaces.admin.gsa.events.GridServiceAgentLifecycleEventListener;
import org.openspaces.admin.gsc.GridServiceContainer;
import org.openspaces.admin.gsc.events.GridServiceContainerLifecycleEventListener;
import org.openspaces.admin.machine.Machine;
import org.openspaces.admin.machine.events.MachineLifecycleEventListener;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.*;
import java.util.logging.Logger;

/**
 * Connect to Admin, listen to events of interest and propagate the events to local listener
 */

public class ClusterWatcher implements MachineLifecycleEventListener, GridServiceAgentLifecycleEventListener, GridServiceContainerLifecycleEventListener, CurrentStateHelper {

    private static final int TASK_THREAD_POOL_SIZE = 5;
    private static final long NODE_RECOVERY_WAIT_SECONDS = 2*60 ;
    private static final long NODE_REBALANCE_WAIT_BEFORE_CONTAINER_CHECK_SECONDS = 30;

    protected Admin admin;

    WatchedResourceGroup currentWatchedGroup;
    WatchedResourceGroup toBeRecreatedWatchGroup;

    //HostAddress -> ContainerInfo
    ConcurrentHashMap<String, ContainerConfiguration> scheduledForCreation;
    //
    ConcurrentHashMap<String, ToBeRebalancedResource> toBeRebalanced;
    // HostAddress -> ContainerStartTask
    ConcurrentHashMap<String, ScheduledFuture<ContainerStarterTask>> scheduledRecreationTasks;

    ConcurrentHashMap<String, ScheduledFuture<MachineRebalanceTask>> scheduledRebalanceTasks;


    //TODO: Determine the followings :-
    // - Number of threads - could come configuration
    // - Separate executors for each task type or a single one with more threads?
    ScheduledExecutorService scheduledExecutorService;

    static Logger logger = Logger.getLogger(ClusterWatcher.class.getName());

    public ClusterWatcher(String username, String password, String locator, String lookupGroup) {

        currentWatchedGroup = new WatchedResourceGroup();
        toBeRecreatedWatchGroup = new WatchedResourceGroup();

        scheduledForCreation = new ConcurrentHashMap<String, ContainerConfiguration>();
        toBeRebalanced = new ConcurrentHashMap<String, ToBeRebalancedResource>();

        scheduledRecreationTasks = new ConcurrentHashMap<String, ScheduledFuture<ContainerStarterTask>>();
        scheduledRebalanceTasks = new ConcurrentHashMap<String, ScheduledFuture<MachineRebalanceTask>>();
        scheduledExecutorService = Executors.newScheduledThreadPool(TASK_THREAD_POOL_SIZE);

        AdminFactory af = new AdminFactory();

        if (locator != null && !"".equals(locator)) {
            af.addLocator(locator);
        }

        if (lookupGroup != null && !"".equals(lookupGroup)) {
            af.addGroup(lookupGroup);
            System.out.println("Added lookup group: " + lookupGroup);
        }

        if (username != null && password != null) {
            af.credentials(username, password);
        }
        admin = af.createAdmin();
        //TOD: The admin listeners get us changes henceforth
        // Still need to get the current status.
        // Having a task that waits to fill all the details might be a good option.
        admin.getGridServiceAgents().addLifecycleListener(this);
        admin.getMachines().addLifecycleListener(this);
        admin.getGridServiceContainers().addLifecycleListener(this);
        logger.info("Started Admin EventCode listening");
    }

    @Override
    public void machineAdded(Machine machine) {
        logger.info("EventCode : Machine Added - " + machine);

        currentWatchedGroup.getMachines().put(machine.getHostAddress(), machine);

        // Check the impact - what action has been done / pending for this node ?

        //Check if this is a 'lost' machine that has come back:
        //          if so, trigger rebalancing.
        ToBeRebalancedResource toBeRebalancedResource = toBeRebalanced.get(machine.getHostAddress());
        if(toBeRebalancedResource != null){
            toBeRebalanced.remove(toBeRebalancedResource);
            MachineRebalanceTask task =  new MachineRebalanceTask(this, toBeRebalancedResource);
            //TODO - wait time comes from configuration
            // Start ticking clock
            ScheduledFuture scheduledFuture = scheduledExecutorService.schedule(task, NODE_REBALANCE_WAIT_BEFORE_CONTAINER_CHECK_SECONDS, TimeUnit.SECONDS);

            //Retain the ability to cancel this task
            scheduledRebalanceTasks.put(machine.getHostAddress(), scheduledFuture) ;
        }
    }

    @Override
    public void machineRemoved(Machine machine) {

        String hostAddress  = machine.getHostAddress();
        String hostName = machine.getHostName();

        logger.info("EventCode : Machine Removed - Host Address: " + hostAddress + " , Host Name: " +  hostName);

        currentWatchedGroup.getMachines().remove(hostAddress);
        toBeRecreatedWatchGroup.getMachines().put(machine.getUid(), machine);

        GridServiceAgent agent = machine.getGridServiceAgent();
        ArrayList<ContainerConfiguration> containerList = new ArrayList<ContainerConfiguration>();

        //Obtain the details to populate options for the container

        // Get the containers corresponding for this machine (they were removed first)
        //TODO: Consider getting these containers when they are added instead of when removed - just in case
        ArrayList<GridServiceContainer> containers = new ArrayList<GridServiceContainer>();
        Iterator<Map.Entry<String, GridServiceContainer>> iterator = toBeRecreatedWatchGroup.getContainers().entrySet().iterator();
        while (iterator.hasNext()){
            Map.Entry<String, GridServiceContainer> entry = iterator.next();
            if(entry.getValue().getMachine().getUid().equals(machine.getUid())){
                containers.add(entry.getValue());
                toBeRecreatedWatchGroup.getContainers().remove(entry.getValue().getUid());
                iterator.remove();

            }
        }
        // Get container com.gigaspaces.odsx.noderebalancer.info needed to restart the containers - VM Arugments, Env. Variables, Zones...
        logger.info("Collecting details of containers from removed machine. Total containers count : " + containers.size());
        for( GridServiceContainer container : containers ){
            String id = container.getId();
            String uid = container.getUid();
            Set<String> zones = container.getExactZones().getZones();

            GridServiceContainerOptions options;
            String[] inputArguments = container.getVirtualMachine().getDetails().getInputArguments().clone();
            Map<String, String> env = container.getVirtualMachine().getDetails().getEnvironmentVariables();

            ContainerOptionsInfo containerOptionsInfo = new ContainerOptionsInfo( inputArguments, env);
            ContainerConfiguration containerInfo = new ContainerConfiguration(id, uid, zones, machine.getHostAddress(), machine.getHostName(), containerOptionsInfo );
            containerList.add(containerInfo);

            //Look up is by host address of the original machine (machine being removed
            scheduledForCreation.put(hostAddress, containerInfo) ;

            logger.fine( " Storing Container information for re-creations: " + containerInfo);
        }


        ContainerStarterTask task =  new ContainerStarterTask(this, containerList);
        //TODO - wait time comes from configuration
        // Start ticking clock
        ScheduledFuture scheduledFuture = scheduledExecutorService.schedule(task, NODE_RECOVERY_WAIT_SECONDS, TimeUnit.SECONDS);

        //Retain the ability to cancel this task
        scheduledRecreationTasks.put(hostAddress, scheduledFuture) ;

    }

    @Override
    public void gridServiceAgentAdded(GridServiceAgent gridServiceAgent) {
        logger.info("EventCode : Service Agent  Added - " + gridServiceAgent);

        currentWatchedGroup.getAgents().put(gridServiceAgent.getUid(), gridServiceAgent);
    }

    @Override
    public void gridServiceAgentRemoved(GridServiceAgent gridServiceAgent) {
        logger.info("EventCode : Service Agent  Removed - " + gridServiceAgent);

        currentWatchedGroup.getAgents().remove(gridServiceAgent.getUid());
    }

    @Override
    public void gridServiceContainerAdded(GridServiceContainer gridServiceContainer) {
        logger.info("EventCode : Service Container  Added - " + gridServiceContainer);

        currentWatchedGroup.getContainers().put(gridServiceContainer.getUid(), gridServiceContainer);
    }

    @Override
    public void gridServiceContainerRemoved(GridServiceContainer gridServiceContainer) {
        logger.info("EventCode : Service Container  Removed - " + gridServiceContainer);

        currentWatchedGroup.getContainers().remove(gridServiceContainer.getUid());
        //TODO: Cleanup the entries being added at a later point
        //      - Based on time
        //      - Size (similar to circular buffer)
        //Note that retrieval is based on machine uid
        toBeRecreatedWatchGroup.containers.put(gridServiceContainer.getUid(),gridServiceContainer );
    }

    //TODO: Should this return more than one machine ? Parital sorting ?
    @Override
    public Machine geMachineWithMostFreeMemory(){
        Machine machines[] = admin.getMachines().getMachines();
        Pair<Machine, Long> machineInfo = new MachineFinder().findMachineWithRAM(machines);
        logger.fine("Selected Machnine with most available RAM : " +  machineInfo.getSecond() + " Bytes -  " + machineInfo.getFirst().getHostAddress());
        return machineInfo.getFirst();
    }

    @Override
    public void addContainerForReBalancing(String targetHostAddress, String targetHostName, ArrayList<ContainerConfiguration> containers) {
        ToBeRebalancedResource resource = new ToBeRebalancedResource(targetHostAddress, targetHostName, containers);
        toBeRebalanced.put(containers.get(0).originalHostAddress,resource);
    }

    @Override
    public Machine getMachine(String hostIP) {
        Machine machine = currentWatchedGroup.machines.get(hostIP);
        return machine;
    }
}

