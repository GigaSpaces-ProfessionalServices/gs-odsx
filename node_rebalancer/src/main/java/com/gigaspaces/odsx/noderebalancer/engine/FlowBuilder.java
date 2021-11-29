package com.gigaspaces.odsx.noderebalancer.engine;

import com.gigaspaces.odsx.noderebalancer.leumiflow.SpaceServerRecoveryFlow;
import com.gigaspaces.odsx.noderebalancer.leumiflow.TieredStorageSpaceServerRecoveryFlow;
import com.gigaspaces.odsx.noderebalancer.model.Flow;
import com.gigaspaces.odsx.noderebalancer.policy.Policy;
import com.gigaspaces.odsx.noderebalancer.policy.ServerConfiguration;

import java.util.Map;
import java.util.logging.Logger;

public class FlowBuilder {

    static Logger logger = Logger.getLogger(FlowBuilder.class.getName());

    public static Flow build(String definition, String name, String ipAddress, Map<String, String> parameters) {
        //TODO: Instead of static checks against known names, use Reflection to instantiated specified class
        Flow flow=null;
        if("com.gigaspaces.odsx.noderebalancer.leumiflow.SpaceServerRecoveryFlow".equals(definition)){
            logger.info("Building SpaceServerRecoveryFlow workflow for server with ip address:  " + ipAddress);
            flow=SpaceServerRecoveryFlow.build(name, ipAddress, parameters);
        }else if("com.gigaspaces.odsx.noderebalancer.leumiflow.TieredStorageSpaceServerRecoveryFlow".equals(definition)){
            logger.info("Building TieredStorageSpaceServerRecoveryFlow workflow for server with ip address:  " + ipAddress);
            flow=TieredStorageSpaceServerRecoveryFlow.build(name, ipAddress, parameters);
        } else {
            logger.info("Can not build recovery flow as the provided definition is not supported :  " + definition);
        }
        if(flow!=null) flow.getContext().setParameters(parameters);
        return flow;
    }
}
