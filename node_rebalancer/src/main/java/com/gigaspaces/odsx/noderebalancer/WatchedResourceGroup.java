package com.gigaspaces.odsx.noderebalancer;

import org.openspaces.admin.gsa.GridServiceAgent;
import org.openspaces.admin.gsc.GridServiceContainer;
import org.openspaces.admin.machine.Machine;

import java.util.concurrent.ConcurrentHashMap;

public class WatchedResourceGroup {

    ConcurrentHashMap<String, GridServiceAgent> agents;
    ConcurrentHashMap<String, Machine> machines;
    ConcurrentHashMap<String, GridServiceContainer> containers;

    public WatchedResourceGroup(){
        agents = new ConcurrentHashMap<String, GridServiceAgent>();
        machines = new ConcurrentHashMap<String, Machine>();
        containers = new ConcurrentHashMap<String, GridServiceContainer>();
    }
    public ConcurrentHashMap<String, GridServiceAgent> getAgents() {
        return agents;
    }

    public void setAgents(ConcurrentHashMap<String, GridServiceAgent> agents) {
        this.agents = agents;
    }


    public ConcurrentHashMap<String, Machine> getMachines() {
        return machines;
    }

    public void setMachines(ConcurrentHashMap<String, Machine> machines) {
        this.machines = machines;
    }



    public ConcurrentHashMap<String, GridServiceContainer> getContainers() {
        return containers;
    }

    public void setContainers(ConcurrentHashMap<String, GridServiceContainer> containers) {
        this.containers = containers;
    }

}
