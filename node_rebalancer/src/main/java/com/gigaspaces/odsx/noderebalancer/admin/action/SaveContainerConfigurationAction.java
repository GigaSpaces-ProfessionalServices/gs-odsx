package com.gigaspaces.odsx.noderebalancer.admin.action;

import com.gigaspaces.odsx.noderebalancer.action.BaseAction;
import com.gigaspaces.odsx.noderebalancer.action.Status;
import com.gigaspaces.odsx.noderebalancer.admin.model.ContainerConfiguration;
import com.gigaspaces.odsx.noderebalancer.model.Context;

import java.util.logging.Level;
import java.util.logging.Logger;

public class SaveContainerConfigurationAction extends BaseAction {


    public SaveContainerConfigurationAction(Context context) {
        super(context, Type.TASK);
    }

    @Override
    public Status callInternal() throws Exception {
        logger.info("Running the  SaveContainerConfigurationAction Action in response to event  : " + getEvent());
        if(event != null && event.getContent() != null && event.getContent() instanceof ContainerConfiguration){
            ContainerConfiguration containerConfiguration = (ContainerConfiguration) event.getContent();
            String zone = "";
            if ( containerConfiguration.zones != null && containerConfiguration.zones.size() == 1) {
                zone = containerConfiguration.zones.toArray()[0].toString();
                Context context = this.getFlowContext();

                if( context.getValue(zone) != null){
                    logger.info(String.format("The Container configuration for zone %s is already present. Will not be updated. ", zone));
                }else {
                    context.setValue(zone, containerConfiguration);
                    logger.info("Saved container configuration for zone :  " + zone);
                }
            } else {
                logger.warning("Did not find expected 1 zone associated with  the container, will not be saved : " + containerConfiguration);
            }
        }else {
            logger.warning("Did not find expected content in the event  " + event);
        }
        return Status.SUCCESS;
    }

}
