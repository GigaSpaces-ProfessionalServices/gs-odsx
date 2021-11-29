package com.bofleumi.gsadmin.wangateway;

import com.bofleumi.gsadmin.MyAdmin;
import com.bofleumi.gsadmin.ObjectType;
import com.bofleumi.gsadmin.util.TableGenerator;
import com.gigaspaces.cluster.activeelection.SpaceMode;
import com.j_spaces.core.filters.ReplicationStatistics;
import org.apache.log4j.Level;
import org.apache.log4j.Logger;
import org.openspaces.admin.gateway.Gateway;
import org.openspaces.admin.gateway.GatewayProcessingUnit;
import org.openspaces.admin.gateway.GatewaySinkSource;
import org.openspaces.admin.gateway.Gateways;
import org.openspaces.admin.space.Space;
import org.openspaces.admin.space.SpaceInstance;
import org.openspaces.admin.space.SpacePartition;
import org.openspaces.core.GigaSpace;
import org.openspaces.core.GigaSpaceConfigurer;
import org.openspaces.core.space.CannotFindSpaceException;
import org.openspaces.core.space.EmbeddedSpaceConfigurer;
import org.openspaces.core.space.SpaceProxyConfigurer;

import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Scanner;
import java.util.concurrent.TimeUnit;

import static com.bofleumi.gsadmin.wangateway.ConstantColor.ANSI_BLACK;
import static com.bofleumi.gsadmin.wangateway.ConstantColor.ANSI_BLUE;
import static com.bofleumi.gsadmin.wangateway.ConstantColor.ANSI_GREEN;
import static com.bofleumi.gsadmin.wangateway.ConstantColor.ANSI_GREEN_BACKGROUND;
import static com.bofleumi.gsadmin.wangateway.ConstantColor.ANSI_RED_BACKGROUND;
import static com.bofleumi.gsadmin.wangateway.ConstantColor.ANSI_RESET;

public class WanGatewayInfo extends MyAdmin {

    private static String[] locators;
    private static String spaceName = "";
    private static String sUsername;
    private static String sPassword;
    private static String sPasswordFilename;
    private static String menu;
    private static TableGenerator tableGenerator = new TableGenerator();
    private static List<String> headersList = new ArrayList<>();
    private static List<List<String>> rowsList = new ArrayList<>();


    public WanGatewayInfo(String username, String password, String passwordFilename, String locator, String menu) {
        this.username = username;
        if (passwordFilename != null) {
            try {
                readPasswordFile(passwordFilename);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        if (password != null) {
            this.password = password;
        }
        this.locator = locator;
        if (menu != null) {
            this.menu = menu;
        }
        initAdmin();
    }

    private void showRedoLogStatistics() {
        System.out.println("Gathering redolog counts...");

        // add appropriate waitFor call
        Space s = admin.getSpaces().waitFor(spaceName, 10, TimeUnit.SECONDS);
        if (s != null) {
            s.waitFor(s.getNumberOfInstances(), SpaceMode.PRIMARY, 10, TimeUnit.SECONDS);
        }

        int spaceCount = 1;
        for (Space space : admin.getSpaces()) {
            SpacePartition partitions[] = space.getPartitions();
            System.out.println(String.format("Space (%d), [%s] :", spaceCount++, space.getName()));
            for (int i = 0; i < partitions.length; i++) {
                SpacePartition partition = partitions[i];
                long redologSize = partition.getPrimary().getStatistics().
                        getReplicationStatistics().getOutgoingReplication().getRedoLogSize();

                System.out.println(String.format("   -> Redo log size for partition [%d] is: %d", partition.getPartitionId(), redologSize));
            }
        }
        System.out.println("*** End redolog counts ***");
        System.out.println();
    }

    public void showNumberOfEntries() {
        System.out.println("Gathering object counts...");

        // add appropriate waitFor call
        Space s = admin.getSpaces().waitFor(spaceName, 10, TimeUnit.SECONDS);
        if (s != null) {
            s.waitFor(s.getNumberOfInstances(), SpaceMode.PRIMARY, 10, TimeUnit.SECONDS);
        }
        int spaceCount = 1;
        for (Space space : admin.getSpaces()) {
            System.out.println(String.format("Space (%d), [%s], numberOfInstances [%d], numberOfBackups [%d]:",
                    spaceCount++, space.getUid(), space.getNumberOfInstances(), space.getNumberOfBackups()));
            System.out.println(String.format("   Stats: Write [ %d (write count), %s (write per second)]",
                    space.getStatistics().getWriteCount(),
                    space.getStatistics().getWritePerSecond()
            ));
            System.out.println("   Instance information...");
            for (SpaceInstance spaceInstance : space) {
                Map<String, Integer> map = spaceInstance.getRuntimeDetails().getCountPerClassName();
                Iterator<String> iter = map.keySet().iterator();
                System.out.println(String.format("   -> SpaceInstance [%s], instanceId [%d], backupId [%d], Mode [%s]",
                        spaceInstance.getUid(), spaceInstance.getInstanceId(), spaceInstance.getBackupId(), spaceInstance.getMode()));

                int classCount = 1;
                while (iter.hasNext()) {
                    String key = iter.next();
                    if (!"java.lang.Object".equals(key)) {
                        System.out.println(String.format("      -> Class (%d) : %s, count: %d", classCount++, key, map.get(key)));
                    }
                }
                System.out.println("      -> Host: "
                        + spaceInstance.getMachine().getHostAddress());
                System.out.println(String.format("      -> Stats: Write [ %d (write count), %s (write per second)]"
                        , spaceInstance.getStatistics().getWriteCount()
                        , spaceInstance.getStatistics().getWritePerSecond()
                ));
                System.out.println("      -> GSC: "
                        // gsc.getId() <= added after 10.2.1
                        + spaceInstance.getVirtualMachine().getGridServiceContainer().getId());

            }
        }
        System.out.println("*** End object counts ***");
        System.out.println();
    }


    public void showDetailWangatewayInfo() {
        Space s = admin.getSpaces().waitFor(spaceName, 10, TimeUnit.SECONDS);
        if (s != null) {
            s.waitFor(s.getNumberOfInstances(), SpaceMode.PRIMARY, 10, TimeUnit.SECONDS);
        }
        Gateways gateways = admin.getGateways();
        String inboundDetails = "Inbound details :  \n-------------------- : \n";
        String outboundDetails = "\n : \nOutbound details :  \n-------------------- : \n";
        int gatewayCount = 1;
        for (Gateway gateway : gateways) {
            inboundDetails += "Gateway Name : " + gateway.getName() + "\n";
            //System.out.println(String.format("Gateway (%d), [%s] :", gatewayCount++, gateway.getName()));
            //System.out.println("   Gateway details...");
            Map<String, GatewayProcessingUnit> map = gateway.getNames();
            Iterator<String> iter = map.keySet().iterator();
            while (iter.hasNext()) {
                String key = iter.next();
                //System.out.println("   -> PU name : " + key);
                GatewaySinkSource[] arrGatewaySinkSource = map.get(key).getSink().getSources();
                if (arrGatewaySinkSource != null) {
                    int gatewaySinkSourceCount = 1;
                    inboundDetails += "Sink Gateway Name : ";
                    for (GatewaySinkSource gatewaySinkSource : arrGatewaySinkSource) {
                        //System.out.println(String.format("   -> Sink gateway (%d), name : %s", gatewaySinkSourceCount++, gatewaySinkSource.getSourceGatewayName()));
                        inboundDetails += gatewaySinkSource.getSourceGatewayName() + ",";
                    }
                    inboundDetails = inboundDetails.substring(0, inboundDetails.length() - 1);
                }
                inboundDetails += "\n";
                inboundDetails += "Discovery port : " + map.get(key).getDiscoveryPort() + "\n";
                inboundDetails += "Communication port : " + map.get(key).getCommunicationPort() + "\n";
                //  System.out.println("   -> Discovery port : " + map.get(key).getDiscoveryPort());
                //  System.out.println("   -> Communication port : " + map.get(key).getCommunicationPort());
            }
        }
        //System.out.println();
        //System.out.println("Outbound details : ");
        int spaceCount = 1;
        for (Space space : admin.getSpaces()) {
            //System.out.println(String.format("Space (%d), [%s] :", spaceCount++, space.getName()));
            SpacePartition partitions[] = space.getPartitions();

            for (int i = 0; i < partitions.length; i++) {
                SpacePartition partition = partitions[i];
                int partitionId = partition.getPartitionId();
                // System.out.println(String.format("   -> Space partition id [%s] :", partitionId));

                long redologSize = partition.getPrimary().getStatistics().
                        getReplicationStatistics().getOutgoingReplication().getRedoLogSize();


                //System.out.println(String.format("      -> Redo log size for partition [%d] is: %d", partitionId, redologSize));

                int channelCount = 1;
                for (ReplicationStatistics.OutgoingChannel channel : partition.getPrimary().
                        getStatistics().
                        getReplicationStatistics().
                        getOutgoingReplication().
                        getChannels(ReplicationStatistics.ReplicationMode.GATEWAY)) {
                    if (channel.getReplicationMode().name().equals("BACKUP_SPACE")) {
                        continue;
                    }
                    String targetShortName = channel.getTargetMemberName().split(":")[1];
                    // System.out.println(String.format("      -> Channel (%d), [%s] :", channelCount++, targetShortName));


                    String remoteHostname = "Not available";
                    String processId = "Not available";
                    String version = "Not available";
                    if (channel.getTargetDetails() != null) {
                        remoteHostname = channel.getTargetDetails().getHostName();
                        version = channel.getTargetDetails().getVersion().toString();
                        processId = "" + channel.getTargetDetails().getProcessId();
                    }
                    /*System.out.println("         -> Remote host : " + remoteHostname);
                    System.out.println("         -> Version : " + version);
                    System.out.println("         -> PID : " + processId);

                    System.out.println("         -> Channel state : " + channel.getChannelState().name());
                    System.out.println("         -> receivedBytesPerSecond : " + channel.getReceiveBytesPerSecond());
                    System.out.println("         -> sendBytesPerSecond : " + channel.getSendBytesPerSecond());
                    System.out.println("         -> SendPacketsPerSecond : " + channel.getSendPacketsPerSecond());*/

                    outboundDetails += "Space Name :" + space.getName() + "\n";
                    outboundDetails += "Partition Id :" + partitionId + "\n";
                    if ("ACTIVE".equals(channel.getChannelState().name())) {
                        outboundDetails += "Channel state :" + ANSI_GREEN_BACKGROUND + channel.getChannelState().name() + ANSI_RESET + "\n";
                    } else {
                        outboundDetails += ANSI_RED_BACKGROUND + "Channel state :" + channel.getChannelState().name() + ANSI_BLACK + "\n";
                    }
                    outboundDetails += "Received Bytes Per Second :" + channel.getReceiveBytesPerSecond() + "\n";
                    outboundDetails += "Send Bytes Per Second :" + channel.getSendBytesPerSecond() + "\n";
                    outboundDetails += "Send Packets Per Second :" + channel.getSendPacketsPerSecond() + "\n";
                }
            }
        }
        if (!inboundDetails.equals("Inbound details \n===========================\n")) {
            for (String line : (inboundDetails + outboundDetails).split("\n")) {
                if (!line.contains(":")) {
                    System.out.println(line);
                } else {
                    rowsList.add(Arrays.asList(line.split(":")));
                }
            }
//            System.out.println(inboundDetails + "\n" + outboundDetails);
        }
        //System.out.println("*** End gateway information ***");
    }

    public static void printUsage() {
        System.out.println("This program is used to check the status of the WAN gateway.");
        System.out.println("Available arguments: are -locators x -spaceName x -username x -password x -passwordFilename x");
        System.out.println("Or -help to print this help.");
        System.out.println("  -locators,      lookup locators. Typically you will specify 3, one for each data center, separated with commas.");
        System.out.println("       Example: -locators server1:4174,server2:4174,server3:4174");
        System.out.println("  -spaceName,     space name. A space name to wait for.");
        System.out.println("       Default: \"Products\"");
        System.out.println("  -username,      username. Include if the XAP cluster is secured.");
        System.out.println("  -password,      password. Include if the XAP cluster is secured.");
        System.out.println("  -passwordFilename, </path/to/password/file>.");
        System.out.println("       Filename of file containing password. Use this if you want the program to read the password from a file.");
        System.exit(0);
    }

    public static void printHeader() {
        if ("list".equals(menu)) {
            headersList.add("WanGw-Id");
            headersList.add("Space Name");
            headersList.add("Type");
            headersList.add("Status");
            headersList.add("No of Instances");
            headersList.add("No of Backups");
            headersList.add("Write count");
            headersList.add("Write count/sec");
//            System.out.println("WanGw-Id\t Space Name\t No of Instances\t Number of Backups\tWrite count\t Write count/sec");
//            System.out.println("================================================================================================================");
        } else if ("show".equals(menu)) {

        }
    }

    public double round(double value, int places) {
        if (places < 0) throw new IllegalArgumentException();

        BigDecimal bd = BigDecimal.valueOf(value);
        bd = bd.setScale(places, RoundingMode.HALF_UP);
        return bd.doubleValue();
    }

    static int spaceCount = 1;
    static String details = "";

    public void list() {
        Space s = admin.getSpaces().waitFor(spaceName, 5, TimeUnit.SECONDS);
        if (s != null) {
//            System.out.println("1q");
            s.waitFor(s.getNumberOfInstances(), SpaceMode.PRIMARY, 5, TimeUnit.SECONDS);
        }

        for (Space space : admin.getSpaces()) {
            //details += spaceCount + "\t " + space.getUid() + "\t\t " + space.getNumberOfInstances() + "\t\t\t " + space.getNumberOfBackups() + "\t\t\t " + space.getStatistics().getWriteCount() + "\t\t" + round(space.getStatistics().getWritePerSecond(), 2);
            String channelStatus = space.getPartitions()[0].getPrimary().getReplicationTargets()[0].getReplicationStatus().toString();
            if ("ACTIVE".equals(channelStatus)) {
                channelStatus = ANSI_GREEN_BACKGROUND + channelStatus + ANSI_RESET;
            } else {
                channelStatus = ANSI_RED_BACKGROUND + channelStatus + ANSI_RESET;
            }
            details += spaceCount + "\t " + space.getUid() + "\t " + (space.getPartitions()[0].getPrimary().getReplicationTargets().length > 0 ? "SOURCE" : "DESTINATION") + "\t " + channelStatus + "\t " + space.getNumberOfInstances() + "\t " + space.getNumberOfBackups() + "\t " + space.getStatistics().getWriteCount() + "\t " + round(space.getStatistics().getWritePerSecond(), 2);
            /*System.out.println(String.format("Space (%d), [%s], numberOfInstances [%d], numberOfBackups [%d]:",
                    spaceCount++, space.getUid(), space.getNumberOfInstances(), space.getNumberOfBackups()));
            System.out.println(String.format("   Stats: Write [ %d (write count), %s (write per second)]",
                    space.getStatistics().getWriteCount(),
                    space.getStatistics().getWritePerSecond()
            ));
            System.out.println("   Instance information...");
            for (SpaceInstance spaceInstance : space) {
                Map<String, Integer> map = spaceInstance.getRuntimeDetails().getCountPerClassName();
                Iterator<String> iter = map.keySet().iterator();
                System.out.println(String.format("   -> SpaceInstance [%s], instanceId [%d], backupId [%d], Mode [%s]",
                        spaceInstance.getUid(), spaceInstance.getInstanceId(), spaceInstance.getBackupId(), spaceInstance.getMode()));

                int classCount = 1;
                while (iter.hasNext()) {
                    String key = iter.next();
                    if (!"java.lang.Object".equals(key)) {
                        System.out.println(String.format("      -> Class (%d) : %s, count: %d", classCount++, key, map.get(key)));
                    }
                }
                System.out.println("      -> Host: "
                        + spaceInstance.getMachine().getHostAddress());
                System.out.println(String.format("      -> Stats: Write [ %d (write count), %s (write per second)]"
                        , spaceInstance.getStatistics().getWriteCount()
                        , spaceInstance.getStatistics().getWritePerSecond()
                ));
                System.out.println("      -> GSC: "
                        // gsc.getId() <= added after 10.2.1
                        + spaceInstance.getVirtualMachine().getGridServiceContainer().getId());

            }*/
            rowsList.add(Arrays.asList(details.split("\t ")));
            //System.out.println(details);
            details = "";
        }
    }

    private static void processArgs(String[] args) {
        int index = args.length;

        if (index >= 2) {
            while (index >= 2) {
                String property = args[index - 2];
                String value = args[index - 1];

                if (property.equalsIgnoreCase("-locators")) {
                    locators = value.split(",");
                } else if (property.equalsIgnoreCase("-spaceName")) {
                    spaceName = value;
                } else if (property.equalsIgnoreCase("-username")) {
                    sUsername = value;
                } else if (property.equalsIgnoreCase("-passwordFilename")) {
                    sPasswordFilename = value;
                } else if (property.equalsIgnoreCase("-password")) {
                    sPassword = value;
                } else if (property.equalsIgnoreCase("-menu")) {
                    menu = value;
                } else {
                    System.out.println("Please enter valid arguments.");
                    printUsage();
                    System.exit(0);
                }

                index -= 2;
            }
        }
    }

    static Map<Integer, Space> count_spacemap = new HashMap<>();

    public void getListOfSpaces(boolean consolePrint) {
        admin.getSpaces().waitFor("", 1, TimeUnit.SECONDS);

        for (Space space : admin.getSpaces()) {
            count_spacemap.put(spaceCount, space);
            if (consolePrint)
                System.out.println(spaceCount + ". " + space.getUid());
        }

    }

    public static GigaSpace getOrCreateSpace(String spaceName, String lookuplocator) {
        if (spaceName == null) {
            System.out.println("Space name not provided - creating an embedded space...");
            return new GigaSpaceConfigurer(new EmbeddedSpaceConfigurer("mySpace")).create();
        } else {
            System.out.printf("Connecting to space %s...%n", spaceName);
            try {
                return new GigaSpaceConfigurer(new SpaceProxyConfigurer(spaceName).lookupLocators(lookuplocator)).create();
            } catch (CannotFindSpaceException e) {
                System.err.println("Failed to find space: " + e.getMessage());
                return null;
            }
        }
    }

    public static void main(String[] args) {
        Logger.getRootLogger().setLevel(Level.OFF);
        /*for (int i = 0; i < args.length; i++) {
            System.out.print(args[i] + " ");
        }*/
        if (args[0].equalsIgnoreCase("-help") || args.length == 0) {
            printUsage();
            System.exit(0);
        }
        processArgs(args);
        int locatorCount = 1;
        printHeader();
        for (String locator : locators) {
            //  System.out.println(String.format("Starting for locator (%d), %s\n", locatorCount++, locator));
            WanGatewayInfo info = new WanGatewayInfo(sUsername, sPassword, sPasswordFilename, locator, menu);
            if ("list".equals(menu)) {
                info.list();
            } else if ("show".equals(menu)) {
                info.showDetailWangatewayInfo();
            } else if ("spacelist".equals(menu)) {
                info.getListOfSpaces(true);
            } else if ("disablereplication".equals(menu)) {
                info.getListOfSpaces(false);
            } else {
                System.exit(0);
            }
            spaceCount++;
//            info.showNumberOfEntries();
//            info.showTargets();

        }
        if ("list".equals(menu)) {
            System.out.println(tableGenerator.generateTable(headersList, rowsList));
        } else if ("show".equals(menu)) {
            headersList.add("Showing details for locator ");
            headersList.add(locators[0]);
            System.out.println(tableGenerator.generateTable(headersList, rowsList));
        } else if ("spacelist".equals(menu)) {
            Scanner sc = new Scanner(System.in);
            System.out.println("Select space to change object control : ");
            String selectedValue = sc.nextLine();
            if (count_spacemap.get(Integer.parseInt(selectedValue)) != null) {
                List<ObjectType> objectTypes = new ArrayList<>();
                Space space = count_spacemap.get(Integer.parseInt(selectedValue));
                GigaSpace gigaSpace = space.getGigaSpace();
                String[] strings = space.getInstances()[0].getRuntimeDetails().getClassNames();
                Integer objCount = 1;
                Map<Integer, ObjectType> count_objecttypemap = new HashMap<>();
                for (String className : strings) {
                    if (className.equals("java.lang.Object")) continue;
                    System.out.println(objCount + ". " + className);
                    ObjectType objectType = gigaSpace
                            .readById(ObjectType.class, className);
                    if (objectType == null) {
                        objectType = new ObjectType(className);
                    }
                    objectTypes.add(objectType);
                    count_objecttypemap.put(objCount, objectType);
                    objCount++;
                }
                System.out.println("Select object type to modify control : ");
                selectedValue = sc.nextLine();
                if (count_objecttypemap.get(Integer.parseInt(selectedValue)) != null) {
                    ObjectType ot = count_objecttypemap.get(Integer.parseInt(selectedValue));
                    //String[] operations = {"Insert", "Update", "Delete"};
                    //Map<Integer, String> count_operationmap = new HashMap<>();
                    System.out.println("Select y/n option for " + count_objecttypemap.get(Integer.parseInt(selectedValue)).getClassName());
                    // System.out.println(ot);

                    //for (int i = 0; i < operations.length; i++) {
                    //Insert
                    System.out.print("Insert [" + (ot.getAllowWrite() != null && ot.getAllowWrite() ? true : false) + "] :");
                    selectedValue = sc.nextLine();
                    if ("y".equals(selectedValue) || "n".equals(selectedValue)) {
                        ot.setAllowWrite("y".equals(selectedValue) ? true : null);
                    }
                    //Update
                    System.out.print("Update [" + (ot.getAllowUpdate() != null && ot.getAllowUpdate() ? true : false) + "] :");
                    selectedValue = sc.nextLine();
                    if ("y".equals(selectedValue) || "n".equals(selectedValue)) {
                        ot.setAllowUpdate("y".equals(selectedValue) ? true : null);
                    }
                    //Delete
                    System.out.print("Delete [" + (ot.getAllowTake() != null && ot.getAllowTake() ? true : false) + "] :");
                    selectedValue = sc.nextLine();
                    if ("y".equals(selectedValue) || "n".equals(selectedValue)) {
                        ot.setAllowTake("y".equals(selectedValue) ? true : null);
                    }
                    gigaSpace.write(ot);
                }

            }
        } else if ("disablereplication".equals(menu)) {
            for (Map.Entry<Integer, Space> entry : count_spacemap.entrySet()) {
                Space space = entry.getValue();
                GigaSpace gigaSpace = space.getGigaSpace();
                System.out.println(ANSI_BLUE + "Disabling replication for space : " + space.getName());
                String[] strings = space.getInstances()[0].getRuntimeDetails().getClassNames();
                for (String className : strings) {
                    if (className.equals("java.lang.Object")) continue;
                    ObjectType objectType = gigaSpace
                            .readById(ObjectType.class, className);
                    if (objectType == null) {
                        objectType = new ObjectType(className);
                    }
                    objectType.setAllowTake(null);
                    objectType.setAllowUpdate(null);
                    objectType.setAllowWrite(null);
                    gigaSpace.write(objectType);
                    System.out.println(ANSI_GREEN + "Disabled replication for object type : " + objectType.getClassName());
                }
            }
            System.out.println(ANSI_GREEN + "Successfully disabled replication across the space");
        }
        //System.out.println("Done with statistics.");
        //System.out.println("================================");
        System.exit(0);
    }
}

