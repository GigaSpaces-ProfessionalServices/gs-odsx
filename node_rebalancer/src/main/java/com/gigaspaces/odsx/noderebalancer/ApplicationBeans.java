package com.gigaspaces.odsx.noderebalancer;

import com.gigaspaces.odsx.noderebalancer.admin.AdminAdapter;
import com.gigaspaces.odsx.noderebalancer.admin.model.AdminConfiguration;
import com.gigaspaces.odsx.noderebalancer.engine.FlowEngine;
import com.gigaspaces.odsx.noderebalancer.event.EventDispatcher;
import com.gigaspaces.odsx.noderebalancer.policy.PolicyConfiguration;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ApplicationBeans {
    @Bean
    @Autowired
    public FlowEngine flowEngine(PolicyConfiguration configuration){
        return new FlowEngine( configuration);
    }

    @Bean
    @Autowired
    public AdminAdapter adminAdapter(AdminConfiguration adminConfiguration, EventDispatcher eventDispatcher){
        return new AdminAdapter(adminConfiguration, eventDispatcher);
    }

}
