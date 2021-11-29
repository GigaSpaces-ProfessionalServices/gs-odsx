import com.gigaspaces.odsx.noderebalancer.ClusterConfigurationReader;
import com.gigaspaces.odsx.noderebalancer.policy.Policy;
import com.gigaspaces.odsx.noderebalancer.policy.PolicyAssociation;
import com.gigaspaces.odsx.noderebalancer.policy.PolicyConfiguration;
import com.gigaspaces.odsx.noderebalancer.policy.ServerConfiguration;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeAll;

import java.io.IOException;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

public class ConfigurationReaderTest {

    public final  String SPACE_POLICY_NAME = "spaceRecoveryPolicy";
    public final  String SPACE_POLICY_DEFINITION = "com.gigaspaces.odsx.noderebalancer.leumiflow.SpaceServerRecoveryFlow";

    public final  String TS_SPACE_POLICY_NAME = "tieredSpaceRecoveryPolicy";
    public final  String TS_SPACE_POLICY_DEFINITION = "com.gigaspaces.odsx.noderebalancer.leumiflow.TieredStorageSpaceServerRecoveryFlow";

    static ClusterConfigurationReader configReader = null;

    @BeforeAll
    public static void setup() throws IOException {
        configReader = new ClusterConfigurationReader("./src/test/resources/recovery_flow_cluster.config");
    }

    @Test
    @Order(1)
    public void testBasicConfigReading(){
        assertNotNull(configReader, "The Configuration Reader object should be not null.");
        PolicyConfiguration policyConfiguration = configReader.getPolicyConfiguration();
        assertNotNull(policyConfiguration, "The Policy Configuration object should not be null" );
    }

    @Test
    @Order(2)
    public void testPolicyConfiguration() throws IOException {
        PolicyConfiguration policyConfiguration = configReader.getPolicyConfiguration();
        assertEquals(2, policyConfiguration.getPolicies().size(), "Two policies should be read from configuration.");
        Policy policy = policyConfiguration.getPolicy(SPACE_POLICY_NAME);
        assertNotNull(policy, "Space Recovery Policy Should not be null");
        assertEquals(policy.getName(), SPACE_POLICY_NAME, "Policy name should match the values used to map it.");
        assertEquals(policy.getDefinition(), SPACE_POLICY_DEFINITION, "Policy definition should be correctly populated.");

        Map<String, String> parameters = policy.getParameters();
        assertNotNull(parameters, "Parameters should be populated for the Space Recovery Policy.");
        assertEquals(3, parameters.size(), "The policy should have same number of parameters as configured");
        assertEquals("15000", parameters.get("waitIntervalAfterServerDown"));

    }

    @Test
    @Order(3)
    public void testPolicyAssociation(){
        PolicyConfiguration policyConfiguration = configReader.getPolicyConfiguration();
        Collection<PolicyAssociation> policyAssociations = policyConfiguration.getPolicyAssociations();
        assertNotNull(policyAssociations, "The policy associations should be configured.");
        assertEquals(2, policyAssociations.size(), "Two policy associations are configured in the config file.");
        for(PolicyAssociation policyAssociation : policyAssociations){
            Policy policy = policyAssociation.getPolicy();
            assertNotNull(policy, "Policy associated with policy association should not be null");
            assertEquals(policy, policyConfiguration.getPolicy(policy.getName()), "Policy specified in the policy association should be also present in the policy collection.");
            String policyAssociationTargetType = policyAssociation.getTargetType();
            assertNotNull(policyAssociationTargetType, "There must be target type specified for policy association");
            assertEquals(policyAssociationTargetType, policy.getType(), "The policy type and the policy association target type must match.");
            List serverConfigurations = policyAssociation.getServerConfigurations();
        }
    }

    @Test
    @Order(4)
    public void testServerConfiguration(){
        PolicyConfiguration policyConfiguration = configReader.getPolicyConfiguration();
        Collection<PolicyAssociation> policyAssociations = policyConfiguration.getPolicyAssociations();
        for(PolicyAssociation policyAssociation : policyAssociations) {
            List<ServerConfiguration> serverConfigurations = policyAssociation.getServerConfigurations();
            assertNotNull(serverConfigurations, "There must be servers configured for a given policy assoication.");
            assertEquals(2, serverConfigurations.size(), "The configuration has two nodes per policy association.");
            for(ServerConfiguration serverConfiguration: serverConfigurations){
                assertNotNull(serverConfiguration.getIpAddress());
                Set<String> zones = serverConfiguration.getZones();
                assertNotNull(zones, "Zones collection should not be null");
                if(serverConfiguration.getIpAddress().equals("10.0.0.109") || serverConfiguration.getIpAddress().equals("10.0.0.192")) {
                    assertTrue(zones.contains("space"), "The zone 'space' should be present");
                    assertEquals(4, serverConfiguration.getZoneContainerCount("space"), "Expected 4 countainers for space zone.");
                } else if(serverConfiguration.getIpAddress().equals("10.0.0.81") || serverConfiguration.getIpAddress().equals("10.0.0.230")) {
                    assertTrue(zones.isEmpty(), "No GSC Configuration");
                    assertNull( serverConfiguration.getZoneContainerCount("service"), "No GSC Configuration");

                }
            }
        }
    }
        //assertEquals( 240, config.getWaitForMachineBeforeContainerRelocation());
        //assertEquals( 4, config.getSpaceServers().length);
        //assertEquals( "10.0.0.56", config.getSpaceServers()[0].getIpAddress());

}


