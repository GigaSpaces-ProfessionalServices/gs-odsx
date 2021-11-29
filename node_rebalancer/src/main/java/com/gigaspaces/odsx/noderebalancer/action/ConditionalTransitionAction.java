package com.gigaspaces.odsx.noderebalancer.action;

import com.gigaspaces.odsx.noderebalancer.model.Context;
import com.sun.org.apache.xpath.internal.operations.Bool;
import org.springframework.expression.Expression;
import org.springframework.expression.ExpressionParser;
import org.springframework.expression.spel.standard.SpelExpressionParser;

import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Based on result of boolean expression evaluation, execute one of the wo provided actions.
 * Purpose: Cause transition from one workflow state to another state.
 *
 * e.g. conditional expression: numberOfContainers < expectedCount
 * if evaluates to true : transition to stable state
 * if evaluates to false: transition to createContainersState
 *
 */
public class ConditionalTransitionAction extends TransitionAction {

    private final String conditionExpression;


    /**
     *
     * @param context - workflow context for exchanging data
     * @param conditionExpression - Transition to be carried out only if the expression evaluates to be truee
     * @param targetState - Transition to this state, only if the condition expressional evaluates to true
     */
    public ConditionalTransitionAction(Context context, String conditionExpression, String targetState) {
        super(context,targetState );
        this.conditionExpression = conditionExpression;
    }



    @Override
    /**
     * The action execution evaluates the expression and based on the outcome, sets the next action.
     */
    public Status callInternal() throws Exception {
        Status returnStatus = Status.FAILURE;
        logger.info(" Starting condition expression evaluation for Conditional Transition  with expression : " + conditionExpression);
        ExpressionParser parser = new SpelExpressionParser();
        Expression exp = parser.parseExpression(conditionExpression);
        Boolean result = (Boolean) exp.getValue(getFlowContext());
        logger.info(" The result of evaluation is  " + result);

        if(result){
            returnStatus = Status.SUCCESS;
        }
        return returnStatus;
    }
}
