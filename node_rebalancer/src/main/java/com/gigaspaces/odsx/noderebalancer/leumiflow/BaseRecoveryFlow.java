package com.gigaspaces.odsx.noderebalancer.leumiflow;

import com.gigaspaces.odsx.noderebalancer.admin.AdminAdapter;
import com.gigaspaces.odsx.noderebalancer.event.Event;
import com.gigaspaces.odsx.noderebalancer.event.EventDescrirptor;
import com.gigaspaces.odsx.noderebalancer.model.Context;
import com.gigaspaces.odsx.noderebalancer.model.Flow;

import java.util.logging.Logger;

public class BaseRecoveryFlow  extends Flow {

    public BaseRecoveryFlow(String name) {
        super(name);
    }

    @Override
    public void updateStatistics(String hostAddress, Event event) {
        if ( EventDescrirptor.EventSpace.ADMIN.equals( event.getEventSpace())) {

                if( AdminAdapter.EventCode.MACHINE_ADDED.getCode() == event.getEventCode()) {
                    this.getContext().setServerUp(true);
                    logger.info(" Updated the global context with serer up to be true for the server :" + hostAddress);
                } else if( AdminAdapter.EventCode.MACHINE_REMOVED.getCode() == event.getEventCode()) {
                    this.getContext().setServerUp(false);
                    logger.info(" Updated the global context with serer up to be false for the server :" + hostAddress);
                }
        }

    }
}
