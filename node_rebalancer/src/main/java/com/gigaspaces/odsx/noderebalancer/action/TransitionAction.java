package com.gigaspaces.odsx.noderebalancer.action;

import com.gigaspaces.odsx.noderebalancer.model.Context;

import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Cause transition from one workflow state to another state.
 */
public class TransitionAction extends BaseAction {

    private String transitionTo;

    /**
     *
     * @param context - workflow context for exchanging data
     * @param targetState - name of the workflow state to transition to
     */
    public TransitionAction(Context context, String targetState) {
        super(context, Type.FLOW);
        transitionTo = targetState;
    }

    /**
     * Return name of the target state this action transitions to
     * @return target state
     */
    public String getTargetState() {
        return transitionTo;
    }

    @Override
    /**
     * The action execution merely returs Status.SUCCESS. The actual action of transitioning is carried out by the \
     * workflow engine.
     */
    public Status callInternal() throws Exception {
        logger.info("Running the Transition Action");

        return Status.SUCCESS;
    }
}
