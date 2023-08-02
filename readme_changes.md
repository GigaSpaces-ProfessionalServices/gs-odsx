### TAU v4.09-tau-release tag
1. Build objectManagement jar from https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/objectManagement
2. Reinstall objecmanagement service
3. Fixed issues include : 
   a. register type, unregister type, add index option 
   b. Checking if backupsPerPartition exists in response of get spaces during create space/tiered space else won't show in list
4. update below property in app.yaml file below ddlCriteriaFileName. Make sure adapters.properties is copied to /dbagigashare/current/object/config/ddlparser/.
   adapterPropertyFileName: adapters.properties
### TAU v4.10-tau-release tag
5. Rebuild objectManagement jar from https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/objectManagement and reinstall objecmanagement service
