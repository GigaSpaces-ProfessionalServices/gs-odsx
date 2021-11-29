package integration;

import com.gigaspaces.odsx.noderebalancer.action.Status;
import com.gigaspaces.odsx.noderebalancer.admin.AdminAdapter;
import com.gigaspaces.odsx.noderebalancer.admin.action.RebalanceAction;
import com.gigaspaces.odsx.noderebalancer.model.Context;
import com.gigaspaces.odsx.noderebalancer.policy.ServerConfiguration;
import org.openspaces.admin.Admin;
import org.openspaces.admin.AdminFactory;

import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.*;

public class ContainerRebalancerTest {


    private static final String IP_ADDRESS_OF_MANAGER = "192.168.0.102" ;
    private static final String IP_ADDRESS_OF_CONTAINER_HOST = "192.168.0.102" ;

    public static void main(String args[]) throws ExecutionException, InterruptedException {
        ContainerRebalancerTest starterTest = new ContainerRebalancerTest();
        starterTest.test(args[1], args[2]);
    }

    private void test(String managerAddress, String containerHostAddress) throws ExecutionException, InterruptedException{
        AdminFactory af = new AdminFactory();
        af.addLocator(managerAddress);
        //af.addGroup("CS_DEV_LUS");

        Admin admin = af.createAdmin();
        AdminAdapter.admin = admin;
        admin.getMachines().waitFor(1);
        admin.getGridServiceContainers().waitFor(4);
        if (admin.getGridServiceAgents().waitFor(1, 25L, TimeUnit.SECONDS)){
           Context context = getContext(containerHostAddress);
            RebalanceAction rebalanceAction = new RebalanceAction(context);
            rebalanceAction.setTargetMachineCollectionKey(AdminAdapter.AdminContextId.SELF_HOST.label);
            ExecutorService executor = Executors.newFixedThreadPool(1);
            Future<Status> future = executor.submit(rebalanceAction);

            executor.shutdown();

        }else{
            System.out.println("No agent  available!");
        }
        admin.close();
    }
    private  Context getContext(String containerHostAddress) {
        List<String> machines = new LinkedList<String>();
        machines.add(containerHostAddress);
        ServerConfiguration serverConfiguration = new ServerConfiguration(containerHostAddress, machines );
        serverConfiguration.addZone("space", 2);
        Context context = new DummyContext(serverConfiguration);
        return context;
    }

    class DummyContext extends Context {
        public DummyContext(ServerConfiguration serverConfiguration){
            super("DUMMY_CONTEXT", null,serverConfiguration );
        }
    }
}
