package com.gigaspaces.odsx.noderebalancer.admin.action;

import com.gigaspaces.odsx.noderebalancer.util.MachineFinder;
import com.gigaspaces.odsx.noderebalancer.action.BaseAction;
import com.gigaspaces.odsx.noderebalancer.action.Status;
import com.gigaspaces.odsx.noderebalancer.admin.AdminAdapter;
import com.gigaspaces.odsx.noderebalancer.model.Pair;
import com.gigaspaces.odsx.noderebalancer.model.Context;
import org.openspaces.admin.Admin;
import org.openspaces.admin.machine.Machine;

public class FindServerAction extends BaseAction {

    public enum Criteria {
        MAX_RAM("MaxRam"),
        LEAST_CPU_USAGE("LeastCpuUsage");
        public final String label;
        Criteria(String label){
            this.label = label;
        }
    }
    Criteria criteria;
    public FindServerAction(Context context, Criteria criteria) {
        super(context, Type.TASK);
        this.criteria = criteria;
    }
    //TODO:
    // How to use criteria ?
    // Return value (Machine info)?
    //  Where, how stored ? How referenced / retrieved later ?
    // How / when / by whom unset ?

    @Override
    public Status callInternal() throws Exception {
        System.out.println("Running the FindServerActions action");
        Admin admin = AdminAdapter.getAdmin();
        Machine machines[] = admin.getMachines().getMachines();
        Pair<Machine, Long> machineInfo = new MachineFinder().findMachineWithRAM(machines);
        logger.fine("Selected Machine with most available RAM : " +  machineInfo.getSecond() + " Bytes -  " + machineInfo.getFirst().getHostAddress());
        //getFlowContext().setValue(AdminAdapter.AdminContextId..label, machineInfo.getFirst());
        return Status.SUCCESS;
    }

}
