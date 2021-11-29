package integration;

import com.gigaspaces.odsx.noderebalancer.action.ConditionalTransitionAction;
import com.gigaspaces.odsx.noderebalancer.action.Status;
import com.gigaspaces.odsx.noderebalancer.action.TransitionAction;
import com.gigaspaces.odsx.noderebalancer.admin.AdminAdapter;
import com.gigaspaces.odsx.noderebalancer.admin.action.CheckContainerAction;
import com.gigaspaces.odsx.noderebalancer.model.Context;
import com.gigaspaces.odsx.noderebalancer.policy.ServerConfiguration;
import org.openspaces.admin.Admin;
import org.openspaces.admin.AdminFactory;
import org.openspaces.admin.machine.Machine;

import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.*;
import java.util.logging.Logger;

import static java.lang.Thread.sleep;

public class ConditionalActionTest {


    private static final String IP_ADDRESS_OF_MANAGER = "192.168.0.104" ;
    private static final String IP_ADDRESS_OF_CONTAINER_HOST = "192.168.0.104" ;

    static Logger logger = Logger.getLogger(ConditionalActionTest.class.getName());

    public static void main(String args[]) throws ExecutionException, InterruptedException {
        ConditionalActionTest conditionalActionTest = new ConditionalActionTest();
        conditionalActionTest.test("true", IP_ADDRESS_OF_MANAGER,IP_ADDRESS_OF_MANAGER);
    }

    private void test(String expression, String managerAddress, String containerHostAddress) throws ExecutionException, InterruptedException{
        AdminFactory af = new AdminFactory();
        af.addLocator(managerAddress);
        //af.addGroup("CS_DEV_LUS");

        Admin admin = af.createAdmin();
        AdminAdapter.admin = admin;
        admin.getMachines().waitFor(1);
        System.out.println(" Got machines: " + admin.getMachines().getSize());
        admin.getGridServiceContainers().waitFor(2, 20, TimeUnit.SECONDS);
        Machine machine = admin.getMachines().getMachineByHostName(containerHostAddress);
        logger.info("Got machine : " + machine);
        if(machine == null ){
            machine = admin.getMachines().getMachines()[0];
            logger.info("Got machine : " + machine);
        }
        if (machine != null ){
            Context context = getContext(containerHostAddress);
            CheckContainerAction checkContainerAction = new CheckContainerAction(context);
            //TODO: Set target host
            //checkContainerAction.setTargetMachineCollectionKey(AdminAdapter.AdminContextId.SELF_HOST.label);
            ExecutorService executor = Executors.newFixedThreadPool(1);
            Future<Status> future = executor.submit(checkContainerAction);
            while (!future.isDone()){
                sleep(1000);
                logger.info("Waiting for action completion : " + future);
            }

            logger.info("Container count saved in the context is: " + context.getValue(CheckContainerAction.CONTAINER_COUNT_KEY));

            TransitionAction transitionToCreateContainersStateAction = new TransitionAction(context,"CrateContainerState");
            String conditionalExpression = " #this.getValue( \"ContainerCountKey\" ) > 0 ";
            ConditionalTransitionAction conditionalAction = new ConditionalTransitionAction(context,conditionalExpression,
                                                                        "Initial" );
            conditionalAction = new ConditionalTransitionAction(context,conditionalExpression,"Final");
            future = executor.submit(conditionalAction);
            while (!future.isDone()){
                sleep(1000);
                logger.info("Waiting for action completion : " + future);
            }
            logger.info(" Result of execution is  " + future.get());

            conditionalExpression = " #this.getValue( \"ContainerCountKey\" ) == null ";
            conditionalAction = new ConditionalTransitionAction(context,conditionalExpression,"Final");
            future = executor.submit(conditionalAction);
            while (!future.isDone()){
                sleep(1000);
                logger.info("Waiting for action completion : " + future);
            }
            logger.info(" Result of execution is  " + future.get());

            conditionalExpression = " #this.getValue( \"ContainerCountKey\" ) == 0 ";
            conditionalAction = new ConditionalTransitionAction(context,conditionalExpression,"Final");
            future = executor.submit(conditionalAction);
            while (!future.isDone()){
                sleep(1000);
                logger.info("Waiting for action completion : " + future);
            }
            logger.info(" Result of execution is  " + future.get());


            executor.shutdown();

        }else{
            logger.info("No containers available on the machine!");
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
