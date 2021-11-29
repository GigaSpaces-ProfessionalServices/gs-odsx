package com.gigaspaces.odsx.noderebalancer.admin.model;

import java.util.HashSet;
import java.util.Set;

public class ContainerConfiguration {
    public final String id;
    public final String uid;
    public final HashSet<String> zones;
    public final ContainerOptionsInfo options;
    public final String originalHostAddress;
    public final String originalHostName;

    public ContainerConfiguration(String id, String uid, Set<String> zones, String hostAddress, String hostName, ContainerOptionsInfo options) {
        this.id = id;
        this.uid = uid;
        this.zones = new HashSet<String>(zones);
        this.options = options;
        this.originalHostAddress = hostAddress;
        this.originalHostName = hostName;

    }

    @Override
    public String toString() {
        return "ContainerConfiguration{" +
                "id='" + id + '\'' +
                ", uid='" + uid + '\'' +
                ", zones=" + zones +
                ", options=" + options +
                '}';
    }

}
