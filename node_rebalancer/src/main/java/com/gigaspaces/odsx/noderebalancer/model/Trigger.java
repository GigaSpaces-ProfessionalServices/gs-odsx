package com.gigaspaces.odsx.noderebalancer.model;

import com.gigaspaces.odsx.noderebalancer.action.BaseAction;
import com.gigaspaces.odsx.noderebalancer.event.Event;
import com.gigaspaces.odsx.noderebalancer.event.EventDescrirptor;

import java.util.LinkedList;
import java.util.List;

public class Trigger {

    EventDescrirptor respondsTo;
    List<BaseAction> actions;

    public Trigger(EventDescrirptor eventDescirptor) {
        respondsTo = eventDescirptor;
        actions = new LinkedList<BaseAction>();
    }
    public void addAction(BaseAction action){
        actions.add(action);
    }
    public List<BaseAction> getActionList(){
        return actions;
    }

    public boolean canRespondTo(Event event){
        if(this.respondsTo.equals(event.getDescriptor())){
                return true;
        }
        return false;
    }

    @Override
    public String toString() {
        return "Trigger{" +
                "respondsTo=" + respondsTo +
                ", actions=" + actions +
                '}';
    }

}
