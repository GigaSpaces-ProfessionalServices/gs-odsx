package com.gigaspaces.odsx.noderebalancer.policy;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

public class PolicyAssociation {
    Policy policy;
    String targetType;
    List<ServerConfiguration> servers;

    public PolicyAssociation(Policy policy) {
        this.policy = policy;
        servers = new ArrayList<ServerConfiguration>();
    }


    public void setTargetType(String targetNodeType) {
        this.targetType = targetNodeType;
    }

    public Policy getPolicy() {
        return policy;
    }

    public String getTargetType() {
        return targetType;
    }

    public List<ServerConfiguration> getServerConfigurations() {
        return servers;
    }

    public void addSeverConfiguration(ServerConfiguration serverConfiguration) {
        servers.add(serverConfiguration);
    }
    @Override
    public String toString() {
        return "PolicyAssociation{" +
                "policy=" + policy.getDefinition() +
                ", targetType='" + targetType + '\'' +
                ", servers=" + servers +
                '}';
    }


}
