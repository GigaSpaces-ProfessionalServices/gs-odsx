package com.gigaspaces.odsx.noderebalancer.action;

import com.gigaspaces.odsx.noderebalancer.event.Event;
import com.gigaspaces.odsx.noderebalancer.model.Context;

import java.util.concurrent.Callable;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Base class for all the actions should derive from to ensure the gneral contract.
 *  1. Actions are Callable which return a Status when they complete the run.
 *  2. Actions have a type - TASK, TIMER or INTERNAL.  A vast majority of actions of type TASK and are run on Executor \
 *    or Timer threads. Exception INTERNAL actions  - internal to the working of the engine e.g. TransitionAction.
 *  3. Actions have access to Flow level Context - a decorated map. This is the mechanism for actions to exchange data \
 *     with events, other actions etc.
 *
 */
public abstract class BaseAction  implements  Callable<Status> {
    String name;
    Type type;
    Context flowContext;
    protected Event event;

    public enum Type {
        FLOW,
        TIME,
        TASK
    };
    protected BaseAction(Context context, Type type){
        this.type = type;
        this.flowContext = context;
    }
    public Type getType(){
        return type;
    }

    protected  Context getFlowContext(){
        return flowContext;
    }

    public void setEvent(Event event) {
        this.event = event;
    }

    protected Event getEvent(){
        return event;
    }


    protected Logger logger = Logger.getLogger(this.getClass().getName());

    @Override
    public Status call() throws Exception {
        try{
            return callInternal();
        }catch (Exception ex){
            ex.printStackTrace();
            log(ex);
        }
        return Status.FAILURE;
    }

    public abstract Status callInternal() throws Exception ;
    
    protected void log(Exception e) {
        logger.log(Level.WARNING, "Exception was not handled by the action, caught by the base action", e);
    }



}
