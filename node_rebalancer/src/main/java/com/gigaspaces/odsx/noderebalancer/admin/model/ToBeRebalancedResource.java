package com.gigaspaces.odsx.noderebalancer.admin.model;

import com.gigaspaces.odsx.noderebalancer.admin.model.ContainerConfiguration;

import java.util.ArrayList;

public class ToBeRebalancedResource {
    public final ArrayList<ContainerConfiguration> containers;
    public final String targetHostAddress;
    public final String targetHostName;

    public ToBeRebalancedResource(String targetHostAddress, String targetHostName, ArrayList<ContainerConfiguration> containers) {
        //TODO Add clone method in the containerInfo ? - Do we need that if it is an immutable class?
        this. targetHostAddress = targetHostAddress;
        this.targetHostName = targetHostName;
        this.containers = containers;
    }
}
