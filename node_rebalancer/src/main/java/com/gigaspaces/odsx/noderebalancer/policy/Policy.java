package com.gigaspaces.odsx.noderebalancer.policy;

import java.util.HashMap;

public class Policy {
    private String name;
    private String type;
    private String description = "";
    private String definition = "";
    private HashMap<String, String> parameters;

    public Policy(String name, String type, String definition) {
        this.name = name;
        this.type = type;
        this.definition = definition;
        parameters = new HashMap<>();

    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getDefinition() {
        return definition;
    }

    public void setDefinition(String definition) {
        this.definition = definition;
    }

    public HashMap<String, String> getParameters() {
        return parameters;
    }

    public String getParameterValue(String name) {
        return parameters.get(name);
    }

    public void setParameters(HashMap<String, String> parameters) {
        this.parameters = parameters;
    }

    public void setParameter(String name, String value) {
        this.parameters.put(name, value) ;
    }

    public String getType() {
        return this.type;
    }

    @Override
    public String toString() {
        return "Policy{" +
                "name='" + name + '\'' +
                ", type='" + type + '\'' +
                ", description='" + description + '\'' +
                ", definition='" + definition + '\'' +
                ", parameters=" + parameters +
                '}';
    }
}
