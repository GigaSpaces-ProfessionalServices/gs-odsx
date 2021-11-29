package com.gigaspaces.odsx.noderebalancer.model;

import com.gigaspaces.odsx.noderebalancer.action.BaseAction;
import com.gigaspaces.odsx.noderebalancer.action.DelayAction;

import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;

public class State {

    String name;
    //List<BaseAction> actions;
    List<Trigger> triggers;

    public State(String name) {
        this.name = name;
        triggers = new LinkedList<Trigger>();
        //actions = new ArrayList<BaseAction>();
    }

    public void addTrigger(Trigger trigger) {
        triggers.add(trigger);
    }

    //public void addAction(BaseAction action) {
    //    actions.add(action);
    //}

    public String getName() {
        return name;
    }

    @Override
    public String toString() {
        return "State{" +
                "name='" + name + '\'' +
                '}';
    }
}
