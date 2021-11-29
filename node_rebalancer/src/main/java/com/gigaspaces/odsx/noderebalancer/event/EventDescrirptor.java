package com.gigaspaces.odsx.noderebalancer.event;

import java.util.Objects;

public class EventDescrirptor {
    public enum EventSpace{
        ADMIN,ALERT,INTERNAL
    }
    EventSpace eventSpace;
    int eventCode;
    public EventDescrirptor(EventSpace eventSpace, int eventCode){
        this.eventSpace = eventSpace;
        this.eventCode = eventCode;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        EventDescrirptor that = (EventDescrirptor) o;
        return eventCode == that.eventCode && eventSpace == that.eventSpace;
    }

    @Override
    public int hashCode() {
        return Objects.hash(eventSpace, eventCode);
    }

    @Override
    public String toString() {
        return "EventDescrirptor{" +
                "eventSpace=" + eventSpace +
                ", eventCode=" + eventCode +
                '}';
    }
}
