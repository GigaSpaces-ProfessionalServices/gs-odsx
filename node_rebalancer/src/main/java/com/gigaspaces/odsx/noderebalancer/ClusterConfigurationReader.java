package com.gigaspaces.odsx.noderebalancer;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.gigaspaces.odsx.noderebalancer.policy.Policy;
import com.gigaspaces.odsx.noderebalancer.policy.PolicyAssociation;
import com.gigaspaces.odsx.noderebalancer.policy.PolicyConfiguration;
import com.gigaspaces.odsx.noderebalancer.policy.ServerConfiguration;

import java.io.File;
import java.io.IOException;
import java.util.*;
import java.util.logging.Logger;

public class ClusterConfigurationReader {

    private PolicyConfiguration policyConfiguration;

    static Logger logger = Logger.getLogger(ClusterConfigurationReader.class.getName());

    public ClusterConfigurationReader(String configFileName) throws IOException{
        this.policyConfiguration = new PolicyConfiguration();
        ObjectMapper objectMapper = new ObjectMapper();
        File configFile = new File(configFileName);
        if (configFile.exists() && configFile.canRead()) {
            JsonNode root = objectMapper.readTree(configFile);
            JsonNode policies = root.at("/cluster/policyConfiguration/policies");
            readPolicies(policies);
            JsonNode policyAssociations = root.at("/cluster/policyConfiguration/policyAssociations");
            readPolicyAssociations(policyAssociations);
        } else {
            logger.warning("Could not read config file, default values will be used.");
        }
    }



    private void readPolicies(JsonNode policies) {
        String name = "", type =  "", definition = "";
        if (policies != null && policies.isArray()) {
            for (JsonNode policyNode : policies) {
                name = type = definition = "";
                name = policyNode.get("name").asText();
                if (name != null && name.length() > 0) {
                    type = policyNode.get("type").asText();
                    if(type != null && type.length() > 0){
                        definition = (policyNode.get("definition") != null) ?  policyNode.get("definition").asText() : null;
                        if(definition != null && definition.length() > 0){
                            Policy policy = new Policy(name, type, definition);
                            policyConfiguration.addPolicy(policy);
                            JsonNode parameterNodes = policyNode.get("parameters");
                            HashMap<String, String> parameters = readParameters(parameterNodes);
                            policy.setParameters(parameters);
                            continue;
                        }
                    }
                }
                logger.warning(String.format(" Missing element(s) in  the policy. name %s , type %s , definition %s .The policy will be ignored. ",  name, type, definition));
            }
        }
        else {
            logger.info("Could not read the JSON path and read policies, policy configuration will be empty.");
        }
    }

    private void readPolicyAssociations(JsonNode policyAssociations) {
        if (policyAssociations != null && policyAssociations.isArray()) {
            String policyName ="", targetNodeType = "";
            for (JsonNode policyAssociationNode : policyAssociations) {
                policyName = targetNodeType = "";
                policyName = (policyAssociationNode.get("policy") == null) ? null :  policyAssociationNode.get("policy").asText();
                if (policyName != null && policyName.length() > 0) {
                    targetNodeType = (policyAssociationNode.get("targetNodeType") == null) ? null :  policyAssociationNode.get("targetNodeType").asText();
                    if(targetNodeType != null && targetNodeType.length() > 0){
                        Policy policy = this.policyConfiguration.getPolicy(policyName);
                        if(policy == null){
                            logger.warning("The policy specified in the policy association not found : name " + policyName);
                            continue;
                        }
                        PolicyAssociation policyAssociation = new PolicyAssociation(policy);
                        policyAssociation.setTargetType(targetNodeType);

                        JsonNode serverNodes = policyAssociationNode.get("nodes");
                        JsonNode gscNodes = policyAssociationNode.get("gsc");
                        readServerConfiguration(policyAssociation, serverNodes, gscNodes);
                        this.policyConfiguration.addPolicyAssociation(policyAssociation);
                        continue;
                    }
                }
                logger.warning(String.format(" Missing elements in  policy association :  policyName %s , targetNodeTpe %s :",  policyName, targetNodeType));
            }
        }else {
                //TODO:// log warning
        }
    }



    private void readServerConfiguration(PolicyAssociation policyAssociation, JsonNode serverNodes, JsonNode gscNodes) {
        List<String> serverIds = new LinkedList<>();
        if (serverNodes != null && serverNodes.isArray()) {
            ArrayNode serverArray = (ArrayNode)  serverNodes;
            for(int i = 0; i < serverArray.size(); i++){
                String serverAddress = getSafeTextValue( serverArray.get(i));
                if(serverAddress != ""){
                    serverIds.add(serverAddress);
                    ServerConfiguration serverConfiguration = new ServerConfiguration(serverAddress, serverIds);
                    policyAssociation.addSeverConfiguration(serverConfiguration);
                }
            }
        }



        /*
The gsc node will be array later, so preserving this code

        if (gscNodes != null && gscNodes.isArray()) {
            ArrayNode gscArray = (ArrayNode)  gscNodes;
            Map<String, Integer> zones = readZones(gscArray);
            for(ServerConfiguration serverConfiguration : policyAssociation.getServerConfigurations()){
                for( Map.Entry<String, Integer> zoneEntry : zones.entrySet()){
                    serverConfiguration.addZone(zoneEntry.getKey(), zoneEntry.getValue());
                }
            }
        }
*/
        if (gscNodes != null && gscNodes.isObject()) {
            ObjectNode gscObjectNode = (ObjectNode)  gscNodes;
            Map<String, Integer> zones = readZones(gscObjectNode);
            for(ServerConfiguration serverConfiguration : policyAssociation.getServerConfigurations()){
                for( Map.Entry<String, Integer> zoneEntry : zones.entrySet()){
                    serverConfiguration.addZone(zoneEntry.getKey(), zoneEntry.getValue());
                }
            }

        }


    }

    private Map<String, Integer> readZones(ObjectNode gscObjectNode) {
        Map<String, Integer> zonesMap = new HashMap<>();
       // for (int i = 0; i < gscArray.size(); i++) {
      //      JsonNode gscNode = gscArray.get(i);
        JsonNode gscNode = gscObjectNode;
        Integer count = Integer.valueOf(getSafeTextValue(gscNode.get("count")));
        JsonNode zonesNode = gscNode.get("zones");

        if (zonesNode != null && zonesNode.isArray()) {
            ArrayNode zonesArray = (ArrayNode) zonesNode;
            for (int j = 0; j < zonesArray.size(); j++) {
                String zone = getSafeTextValue(zonesArray.get(j));
                if(zone.length() > 0 ){
                    zonesMap.put(zone, count);
                }
            }
        }
//    }
        return zonesMap;
    }

    private HashMap<String, String> readParameters(JsonNode parametersNode) {
       HashMap<String, String> parametersMap =new HashMap<>();
        if (parametersNode != null && parametersNode.isContainerNode()) {
            Iterator<Map.Entry<String, JsonNode>> it = parametersNode.fields();
            while (it.hasNext()) {
                Map.Entry<String, JsonNode> field = it.next();
                //process every field in the array
                String value = field.getValue().asText();
                if(value != null & value.length() > 0) {
                    parametersMap.put(field.getKey(),  value);
                }
            }
        } else {
            logger.warning("Parameters are not configured correctly, will be ignored.");
        }
        return parametersMap;
    }


    public PolicyConfiguration getPolicyConfiguration() {
        return this.policyConfiguration;
    }

    private String getSafeTextValue(JsonNode textNode){
        String textValue = "";
        if(textNode != null && textNode.asText() != null){
            textValue = textNode.asText();
        }
        return textValue;
    }
}