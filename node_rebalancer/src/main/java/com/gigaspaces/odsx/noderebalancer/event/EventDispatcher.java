package com.gigaspaces.odsx.noderebalancer.event;

import com.gigaspaces.odsx.noderebalancer.admin.model.ContainerConfiguration;

public interface EventDispatcher {
    void dispatchEvent( String hostAddress, Event event);
}
