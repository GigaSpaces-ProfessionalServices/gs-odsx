package com.gigaspaces.odsx.noderebalancer.policy;

import java.util.Collection;
import java.util.HashMap;
import java.util.logging.Logger;

public class PolicyConfiguration {
    private HashMap<String, Policy> policies;
    private HashMap<Policy, PolicyAssociation> policyAssociations;

     Logger logger = Logger.getLogger(PolicyConfiguration.class.getName());

    public PolicyConfiguration(){
        policies = new HashMap<>();
        policyAssociations = new HashMap<>();
    }

    public void addPolicy(Policy policy){
        policies.put(policy.getName(), policy);
    }

    public Policy getPolicy(String policyName) {
        return policies.get(policyName);
    }

    public Collection<Policy> getPolicies(){
        return policies.values();
    }




    public void addPolicyAssociation(PolicyAssociation policyAssociation) {
        policyAssociations.put(policyAssociation.policy,policyAssociation);
    }

    public boolean isValid() {
        return validate();
    }

    private boolean validate() {
        boolean valid = true;
        if( policies.size() == 0 ){
            valid = false;
            logger.info(" There are no policies configured. ");
        }
        if( policyAssociations.size() == 0 ){
            valid = false;
            logger.info(" There are no policy associations configured. ");
        }
        return valid;
    }

    public Collection<PolicyAssociation> getPolicyAssociations() {
        return this.policyAssociations.values();
    }
}
