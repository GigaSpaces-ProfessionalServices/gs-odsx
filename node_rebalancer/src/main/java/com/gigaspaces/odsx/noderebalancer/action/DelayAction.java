package com.gigaspaces.odsx.noderebalancer.action;

import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * This action causes action execution flow to stop for the specified duration.
 * In current implementation, the action is scheduled for execution after the period specified in the parameter  \
 * dela.
 */
public class DelayAction extends BaseAction {

    private long delay; //ms

    /**
     *
     * @param delay - number of milliseconds to delay during execution, after which the action will return
     */
    public DelayAction(Long delay){
        //Context is not required for delay action
        super(null, Type.TIME);
        this.delay = delay;
    }

    public long getDelay(){
        return delay;
    }

    @Override
    public Status callInternal() throws Exception {
        //The actual delay is the delay caused during wait on the ScheduledExecutor
        logger.info(String.format("Synchronous Delay of %s ms completing.", this.delay));
        return Status.SUCCESS;
    }

    @Override
    public String toString() {
        return "DelayAction{" +
                "delay=" + delay +
                '}';
    }

}
