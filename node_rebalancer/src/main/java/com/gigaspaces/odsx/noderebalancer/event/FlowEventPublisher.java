package com.gigaspaces.odsx.noderebalancer.event;

public interface  FlowEventPublisher {
    public void enqueue(Event event) ;
}
