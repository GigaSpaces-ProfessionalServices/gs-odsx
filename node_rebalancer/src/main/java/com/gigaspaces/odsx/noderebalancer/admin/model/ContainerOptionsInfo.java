package com.gigaspaces.odsx.noderebalancer.admin.model;

import java.util.*;

public class ContainerOptionsInfo {
    final public Map<String, String> environmentVariables;
    final public ArrayList<String > vmArguments;
    final public String envVariables[] = {"GS_GSC_OPTIONS", "GS_LOOKUP_GROUPS"};
    public ContainerOptionsInfo(String [] args, Map<String, String> env){
        vmArguments = new ArrayList<String>();
        for (String vmArgument : args){
            if( vmArgument.startsWith("-Xm")){
                vmArguments.add(vmArgument);
            }
        }

        environmentVariables = new HashMap<String, String> ();
        for( String environmentVariable : envVariables){
            String environmentVariableValue = env.get(environmentVariable);
            if (environmentVariableValue != null){
                environmentVariables.put(environmentVariable, environmentVariableValue);
            }
        }
    }

    @Override
    public String toString() {
        return "ContainerOptionsInfo{" +
                "environmentVariables=" + environmentVariables +
                ", vmArguments=" + vmArguments +
                '}';
    }
}
