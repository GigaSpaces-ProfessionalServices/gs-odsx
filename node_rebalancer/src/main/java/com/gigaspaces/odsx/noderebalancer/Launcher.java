package com.gigaspaces.odsx.noderebalancer;


import com.gigaspaces.odsx.noderebalancer.admin.model.AdminConfiguration;
import com.gigaspaces.odsx.noderebalancer.engine.FlowEngine;
import com.gigaspaces.odsx.noderebalancer.policy.PolicyConfiguration;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;

import java.io.IOException;
import java.util.logging.Logger;

public class Launcher {

    protected String[] locators ={""};
    protected String lookupGroup;
    protected String userName;
    protected String password;
    protected String passwordFilename;
    protected String clusterConfigurationFileName;

    static Logger logger = Logger.getLogger(Launcher.class.getName());

    public Launcher() {

    }


    public static void printUsage() {
        System.out.println("This program is used to listen for Admin Events.");
        System.out.println("Available arguments: are -locators x -spaceName x -username x -password x -passwordFilename x");
        System.out.println("Or -help to print this help.");
        System.out.println("  -lookupgroup,      lookup group name.");
        System.out.println("  -locators,      lookup locators. Typically you will specify 3, one for each data center, separated with commas.");
        System.out.println("       Example: -locators server1:4174,server2:4174,server3:4174");
        System.out.println("  -username,      username. Include if the XAP cluster is secured.");
        System.out.println("  -password,      password. Include if the XAP cluster is secured.");
        System.out.println("  -passwordFilename, </path/to/password/file>.");
        System.out.println("       Filename of file containing password. Use this if you want the program to read the password from a file.");
        System.out.println("  -configurationFileName, </path/to/password/file>.");
        System.out.println("       The Cluster Configuration File, containing layout of servers to be monitored and recovery policies..");

        System.exit(0);
    }


    private  void processArgs(String[] args) {
        int index = args.length;

        if (index >= 2) {
            while (index >= 2) {
                String property = args[index - 2];
                String value = args[index - 1];

                if (property.equalsIgnoreCase("-locators")) {
                    locators = value.split(",");
                }else if (property.equalsIgnoreCase("-username")) {
                   userName = value;
                } else if (property.equalsIgnoreCase("-passwordFilename")) {
                    passwordFilename = value;
                } else if (property.equalsIgnoreCase("-password")) {
                    password = value;
                } else if (property.equalsIgnoreCase("-lookupgroup")) {
                    lookupGroup = value;
                }  else if (property.equalsIgnoreCase("-configurationFileName")) {
                    clusterConfigurationFileName = value;
                }else {
                    System.out.println("Please enter valid arguments.");
                    printUsage();
                    System.exit(0);
                }

                index -= 2;
            }
        }
    }


    public static void main(String[] args) {

        Launcher launcher = new Launcher();

        launcher.processArgs(args);

        if( !launcher.validateArguments()){
            logger.severe("Insufficient arguments provided. Please run again with required information.");
            System.out.println("Insufficient arguments provided. Please run again with required information. Please check logs for more details.");
            System.exit(-1);
        }

        ClusterConfigurationReader configurationReader = null;
        try{
            configurationReader = new ClusterConfigurationReader(launcher.clusterConfigurationFileName);
        }catch (IOException ioException){
            logger.severe( "IOException while reading the config file, program will not start." + ioException);
            ioException.printStackTrace();
            System.exit(-1);
        }

        if(configurationReader  == null || configurationReader.getPolicyConfiguration() == null){
            logger.severe( "Could not read Configuration, will exit.");
            System.exit(-1);
        } else if( configurationReader.getPolicyConfiguration().isValid() == false){
            logger.severe( "Invalid policyconfiguration, will exit.");
            System.exit(-1);
        }

        final PolicyConfiguration policyConfiguration = configurationReader.getPolicyConfiguration();
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext();
        context.registerBean(PolicyConfiguration.class, ()->  policyConfiguration);
        context.registerBean(AdminConfiguration.class, launcher.userName, launcher.password, launcher.locators, launcher.lookupGroup );
        context.registerBean(ApplicationBeans.class);
        context.refresh();
        System.out.println("Lookup Group: " + launcher.lookupGroup);
        logger.info("Starting the recovery monitor process, Lookup Group is: " + launcher.lookupGroup);

        FlowEngine flowEngine = context.getBean(FlowEngine.class);

        Thread engineRunner = new Thread(){
            @Override
           public void run(){
                flowEngine.run();
            }
        };
        engineRunner.run();

        //Thread.currentThread().setDaemon(true);

        context.registerShutdownHook();

        Runtime.getRuntime().addShutdownHook(new Thread(new Runnable(){
            @Override
            public void run()
            {
                System.out.println("Shutdown Hook Invoked");
                logger.info("Shutdown hook invoked.");
                flowEngine.initiateShutDown();
            }
        }));


    }

    private boolean validateArguments() {
        boolean hasRequiredArguments = true;
        if(isNullOrEmpty(clusterConfigurationFileName)){
            logger.warning(" Missing required argument : Cluster configuration File Path.");
            hasRequiredArguments = false;
        }
        if(isNullOrEmpty(locators ) && isNullOrEmpty(lookupGroup)){
            logger.warning(" Missing required argument : Either lookupGroup or locator must be provided.");
            hasRequiredArguments = false;
        }
        return hasRequiredArguments;
    }

    private boolean isNullOrEmpty(String string){
        return (string == null || string.length() == 0);
    }

    private boolean isNullOrEmpty(String strings[]){
        return (strings == null || strings.length == 0 || strings[0].length() == 0);
    }

}

