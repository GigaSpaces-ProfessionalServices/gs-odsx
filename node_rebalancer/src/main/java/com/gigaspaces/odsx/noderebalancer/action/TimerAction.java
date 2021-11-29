package com.gigaspaces.odsx.noderebalancer.action;

import com.gigaspaces.odsx.noderebalancer.event.Event;
import com.gigaspaces.odsx.noderebalancer.event.EventDescrirptor;
import com.gigaspaces.odsx.noderebalancer.model.Context;
import com.gigaspaces.odsx.noderebalancer.model.Flow;

import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * Asynchronous Timer
 */
public class TimerAction  extends  BaseAction {

    private long delay ;

    public TimerAction(Context context, long delay) {
        //Context is not required for delay action
        super(context, Type.TIME);
        this.delay = delay;
    }

    public long getDelay(){
        return delay;
    }

    @Override
    public Status callInternal() throws Exception {
        //The actual delay is the delay caused during wait on the ScheduledExecutor
        logger.info(String.format("Triggering TIMER event after asynchronous delay of %s ms completed.", delay));
        Event event = new Event(new EventDescrirptor(EventDescrirptor.EventSpace.INTERNAL, Flow.EventCode.ASYNC_TIMER_COMPLETED.code ), delay);
        getFlowContext().publishInternalEvent(event);
        return Status.SUCCESS;
    }


    @Override
    public String toString() {
        return "TimerAction{" +
                "delay=" + delay +
                '}';
    }
}
