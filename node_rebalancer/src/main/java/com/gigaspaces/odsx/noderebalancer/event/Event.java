package com.gigaspaces.odsx.noderebalancer.event;

public class Event {
    EventDescrirptor descriptor;
    Object content;
    public Event(EventDescrirptor descriptor, Object content){
        this.descriptor = descriptor;
        this.content = content;
    }

    public EventDescrirptor.EventSpace getEventSpace() {
        return descriptor.eventSpace;
    }

    public int getEventCode() {
        return descriptor.eventCode;
    }

    public Object getContent() {
        return content;
    }

    public EventDescrirptor getDescriptor() {
        return descriptor;
    }

    @Override
    public String toString() {
        return "EventCode{" +
                "descriptor=" + descriptor +
                ", content=" + content +
                '}';
    }
}
