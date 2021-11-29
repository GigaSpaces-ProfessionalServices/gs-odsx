package integration;

import com.gigaspaces.odsx.noderebalancer.action.Status;
import com.gigaspaces.odsx.noderebalancer.admin.AdminAdapter;
import com.gigaspaces.odsx.noderebalancer.admin.action.CreateContainerAction;
import com.gigaspaces.odsx.noderebalancer.model.Context;
import com.gigaspaces.odsx.noderebalancer.policy.ServerConfiguration;
import org.openspaces.admin.Admin;
import org.openspaces.admin.AdminFactory;
import org.openspaces.admin.gsa.GridServiceAgent;
import org.openspaces.admin.gsa.GridServiceContainerOptions;
import org.openspaces.admin.gsc.GridServiceContainer;

import java.util.LinkedList;
import java.util.concurrent.*;

public class ContainerStarterTest {
    public static void main(String args[]) throws ExecutionException, InterruptedException {
        ContainerStarterTest starterTest = new ContainerStarterTest();
        starterTest.test();
    }

    private void test() throws ExecutionException, InterruptedException{
        AdminFactory af = new AdminFactory();
        af.addGroup("CS_DEV_LUS");

        Admin admin = af.createAdmin();
        AdminAdapter.admin = admin;
        if (admin.getGridServiceAgents().waitFor(1, 25L, TimeUnit.SECONDS)){
            GridServiceAgent agent = admin.getGridServiceAgents().waitForAtLeastOne();
            System.out.println("Agent Id where the container is being started: " + agent.getUid());
            GridServiceContainerOptions options = new GridServiceContainerOptions();

//            ContainerConfiguration containerConfiguration = new ContainerConfiguration();
//            containerConfiguration.zones.add("space");
//            ContainerOptionsInfo containerOptionInfo= new ContainerOptionsInfo({""} , new HashMap<String, String>());

            Context context = getContext();
            CreateContainerAction createContainerAction = new CreateContainerAction(context);
            createContainerAction.setTargetMachineCollectionKey(AdminAdapter.AdminContextId.SELF_HOST.label);
            ExecutorService executor = Executors.newFixedThreadPool(1);
            Future<Status> future = executor.submit(createContainerAction);
            Status result = future.get();
            if (Status.SUCCESS == result){
                if( admin.getGridServiceAgents().waitForAtLeastOne().getGridServiceContainers().waitFor(1,25L, TimeUnit.SECONDS)){
                    GridServiceContainer shouldBeThere = admin.getGridServiceAgents().waitForAtLeastOne().getGridServiceContainers().getContainers()[0];
                    System.out.println(shouldBeThere);
                    System.out.println(" UID  of the container created: " + shouldBeThere.getUid());
                    System.out.println(" Id  of the container created: " + shouldBeThere.getId());
                } else {
                    System.out.println("Could not create container.");
                }
            }else {
                System.out.println("Failed test");
            }
            executor.shutdown();

        }else{
            System.out.println("No agent  available!");
        }
        admin.close();
    }
    private  Context getContext() {
        ServerConfiguration serverConfiguration = new ServerConfiguration("192.168.56.1", new LinkedList<String>());
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
