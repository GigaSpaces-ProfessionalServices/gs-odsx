package com.gigaspaces.odsx.noderebalancer.admin;

import com.gigaspaces.odsx.noderebalancer.admin.model.AdminConfiguration;
import com.gigaspaces.odsx.noderebalancer.admin.model.ContainerConfiguration;
import com.gigaspaces.odsx.noderebalancer.event.*;
import com.gigaspaces.odsx.noderebalancer.admin.model.ContainerOptionsInfo;
import org.openspaces.admin.Admin;
import org.openspaces.admin.AdminFactory;
import org.openspaces.admin.gsa.GridServiceAgent;
import org.openspaces.admin.gsa.GridServiceContainerOptions;
import org.openspaces.admin.gsa.events.GridServiceAgentLifecycleEventListener;
import org.openspaces.admin.gsc.GridServiceContainer;
import org.openspaces.admin.gsc.events.GridServiceContainerLifecycleEventListener;
import org.openspaces.admin.machine.Machine;
import org.openspaces.admin.machine.events.MachineLifecycleEventListener;

import java.util.Map;
import java.util.Set;
import java.util.logging.Logger;

/**
 * Facade representing the Gigaspaces Admin Client.
 *
 */
public class AdminAdapter implements GridServiceAgentLifecycleEventListener, MachineLifecycleEventListener, GridServiceContainerLifecycleEventListener {

    /**
     * The Admin singleton instance. From time when the Spring IoC was not integrated with this project.
     * Now perhaps this could be retrieved from Spring App Context.
     */
    public static Admin admin;

    /**
     * Event dispatcher is responsible for dispatching event to event queue from where it can \\
     * finally reach its destination.
     */
    EventDispatcher eventDispatcher;

    public static void shutDown() {
        if(getAdmin() == null){
            getAdmin().close();
        }

    }

    /**
     * Event codes for events occurring from the Admin Component.
     */
    public enum EventCode {
        MACHINE_ADDED(11001),
        MACHINE_REMOVED(11002),
        CONTAINER_ADDED(11011),
        CONTAINER_REMOVED(11012);
        public final int code;
        EventCode(int code){
            this.code = code;
        }

        public int getCode() {
            return code;
        }
    }

    /**
     * These are simply "Well-Known" keys which are used to store information originating from Admin events in the
     * workflow level Context (a decorated String -> Object hashmap), so that it is available for later use.
     */
    public enum EventContextId{
        CONTAINER_COLLECTION("ContainerCollectionFromEvent"),
        SERVER_UP_IP_ADDRESS("ServerUpIPAddress");
        public final String label;
        private EventContextId(String label){
            this.label = label;
        }
    };

    /**
     * These are simply "Well-Known" keys which are used to store information in workflow  level Context
     * (a decorated String -> Object hashmap).  Typically, some actions will store the information in  context so that it
     * could be consumed by actions occurring later in the workflow life cycle.
     *      */
    public enum AdminContextId{
        CONTAINER_COLLECTION("ContainerCollectionSaved"),
        RELOCATED_CONTAINER_MARKER("relocated"),
        RESTORED_CONTAINER_MARKER("restored"),
        NO_CONTAINER_MARKER("none"),
        RELOCATED_CONTAINERS_TARGET_HOSTS("TheInterimHosts"),
        SELF_HOST("TheWorkflowOwnerHost");
        public final String label;
        private AdminContextId(String label){
            this.label = label;
        }
    };

    Logger logger = Logger.getLogger(AdminAdapter.class.getName());

    public AdminAdapter(AdminConfiguration adminConfiguration, EventDispatcher eventDispatcher){

        this.eventDispatcher = eventDispatcher;

        AdminFactory af = new AdminFactory();

        if (adminConfiguration.getLocators() != null && adminConfiguration.getLocators().length > 0) {
            for( String locator : adminConfiguration.getLocators()){
                af.addLocator(locator);
            }
        }

        if (adminConfiguration.getLookupGroup() != null && !"".equals(adminConfiguration.getLookupGroup())) {
            af.addGroup(adminConfiguration.getLookupGroup());
            System.out.println("Added lookup group: " + adminConfiguration.getLookupGroup());
        }

        if (adminConfiguration.getUserName() != null && adminConfiguration.getPassword() != null) {
            af.credentials(adminConfiguration.getUserName(), adminConfiguration.getPassword());
        }
        admin = af.createAdmin();
        //TOD: The admin listeners get us changes henceforth
        // Still need to get the current status.
        // Having a task that waits to fill all the details might be a good option.
        //admin.getGridServiceAgents().addLifecycleListener(this);
        admin.getMachines().addLifecycleListener(this);
        admin.getGridServiceContainers().addLifecycleListener( this);
        logger.info("Started Admin EventCode listening");
    }

    public static Admin getAdmin() {
        return admin;
    }

    @Override
    public void gridServiceAgentAdded(GridServiceAgent gridServiceAgent) {

    }

    @Override
    public void gridServiceAgentRemoved(GridServiceAgent gridServiceAgent) {

    }

    @Override
    public void machineAdded(Machine machine) {
        logger.info("Admin EventCode - Machine added :  " + machine.getHostAddress());
        Event event = new Event(new EventDescrirptor(EventDescrirptor.EventSpace.ADMIN, EventCode.MACHINE_ADDED.code), machine.getHostAddress());
        eventDispatcher.dispatchEvent( machine.getHostAddress(), event);
    }

    @Override
    public void machineRemoved(Machine machine) {
        logger.info("Admin EventCode - Machine removed :  " + machine.getHostAddress());

        Event event = new Event(new EventDescrirptor(EventDescrirptor.EventSpace.ADMIN, EventCode.MACHINE_REMOVED.code), machine.getHostAddress());
        eventDispatcher.dispatchEvent( machine.getHostAddress(), event);
    }

    @Override
    public void gridServiceContainerAdded(GridServiceContainer container) {
        logger.info("Admin EventCode - Continaer added :  " + container);
        ContainerConfiguration containerConfiguration = getContainerConfiguration(container);
        Event event = new Event(new EventDescrirptor(EventDescrirptor.EventSpace.ADMIN, EventCode.CONTAINER_ADDED.code), containerConfiguration);
        eventDispatcher.dispatchEvent( container.getMachine().getHostAddress(), event);

    }

    @Override
    public void gridServiceContainerRemoved(GridServiceContainer container) {
        logger.info("Admin EventCode - Container removed :  " + container);
        ContainerConfiguration containerConfiguration = getContainerConfiguration(container);
        Event event = new Event(new EventDescrirptor(EventDescrirptor.EventSpace.ADMIN, EventCode.CONTAINER_REMOVED.code), containerConfiguration);
        eventDispatcher.dispatchEvent( container.getMachine().getHostAddress(), event);
    }

    private ContainerConfiguration getContainerConfiguration(GridServiceContainer container) {
        String id = container.getId();
        String uid = container.getUid();
        Set<String> zones = container.getExactZones().getZones();
        Machine machine = container.getMachine();

        GridServiceContainerOptions options;
        String[] inputArguments = container.getVirtualMachine().getDetails().getInputArguments().clone();
        Map<String, String> env = container.getVirtualMachine().getDetails().getEnvironmentVariables();

        ContainerOptionsInfo containerOptionsInfo = new ContainerOptionsInfo( inputArguments, env);
        return new ContainerConfiguration(id, uid, zones, machine.getHostAddress(), machine.getHostName(), containerOptionsInfo );
    }


}
