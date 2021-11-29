package com.gigaspaces.odsx.noderebalancer.policy;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class ServerConfiguration {
    String serverIpAddress;
    Map<String, Integer> zones;

    /**
     * List of IP Addresses of the servers in the same group,e.g. the nodes which are associated with the same policy.
     * The server are most likely to be grouped by server type e.g. Space, North Bound, CDC, Stream etc.
     */
    private List<String> serverGroup;


    public ServerConfiguration(String address, List<String> serverIds){

        this.serverIpAddress = address;
        this.serverGroup = serverIds;

        zones = new HashMap<>();
    }

    public void addZone(String zone, int count){
        zones.put(zone, count);
    }

    public String getIpAddress(){
        return serverIpAddress;
    }

    public Set<String> getZones() {
        return this.zones.keySet();
    }

    public Integer getZoneContainerCount(String zone) {
        return zones.get(zone);
    }

    public List<String> getServerGroup() {
        return this.serverGroup;
    }
}
