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
### TAU v4.11-tau-release tag
6. Add below properties in app.config with appropriate values :
   app.newspace.creategsc.gscperhost
   app.newspace.creategsc.gscmemory
   app.newspace.creategsc.gsczone
   app.newspace.creategsc.specifichost
   app.newspace.wantspaceproperty
   app.newspace.spaceproperty.filepath.target
   app.newspace.pu.zone
   app.newspace.pu.name
   app.newspace.pu.maxinstancepermachine
7. Add new file /dbagigashare/current/object/config/ddlparser/batchIndexes.txt with below sample values
   STUD.TA_PERSON  SHEM_EMTZAI_ENG EQUAL
   STUD.TA_PERSON  SHEM_MISHP_ENG  ORDERED
8. Update app.yaml file add indexBatchFileName: batchIndexes.txt below adapterPropertyFileName property
9. Rebuild objectManagement jar from https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/objectManagement and reinstall objecmanagement service
### TAU v4.13-tau-release tag
10. Update app.yaml - Add section for oracle same as mssql section. Specify oracleJarFile: OracleFeeder-1.0-SNAPSHOT.jar
11. Update app.config with following values
    app.dataengine.oracle-feeder.oracle.server=
    app.dataengine.oracle-feeder.oracle.username=
    app.dataengine.oracle-feeder.oracle.password=
    app.dataengine.oracle-feeder.oracle.databasename=
    app.dataengine.oracle-feeder.gscperhost=1
    app.dataengine.oracle-feeder.gsc.memory=256m
    app.dataengine.oracle-feeder.gsc.create=y
    app.dataengine.oracle-feeder.sqlite.dbfile=/dbagigawork/sqlite/oracleFeeder.db
    app.dataengine.oracle-feeder.space.name=dih-tau-space
    app.dataengine.oracle-feeder.writeBatchSize=10000
    app.dataengine.oracle-feeder.sleepAfterWriteInMillis=500
12. Rebuild OracleFeeder-1.0-SNAPSHOT jar from https://github.com/GigaSpaces-ProfessionalServices/TAU/tree/master/apps/OracleFeeder and place it to /dbagigashare/current/oracle/jars/
13. Copy load data scripts from https://jay-dalal.s3.us-west-2.amazonaws.com/odsx/tau-feeder-scripts/oracle/ to /dbagigashare/current/oracle/scripts/
    
     Example: load_TA_PERSON.sh
      ```
      echo "starting TA_PERSON"
      table_name="STUD.TA_PERSON"
      exclude_columns="IS_IDNO_OBFUSCATE,IS_PASSPORT_OBFUSCATE"
      pk_columns="K_PNIMI"
      curl -XPOST "http://$1:$2/table-feed/start?table-name=${table_name}&base-column=T_IDKUN&exclude-columns=${exclude_columns}&pk-columns=${pk_columns}"
      ```
14. Rebuild objectManagement jar from https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/objectManagement and reinstall objecmanagement service 
### TAU v4.14-tau-release tag
15. Update app.config
    Change key from app.dataengine.mssql-feeder.gscperhost to app.dataengine.mssql-feeder.gscpercluster
    Change key from app.dataengine.oracle-feeder.gscperhost to app.dataengine.oracle-feeder.gscpercluster
### TAU v4.21-tau-release tag
16. Update app.config with following values
    app.dataengine.mssql-feeder.mssql.server=
    app.dataengine.mssql-feeder.mssql.username=
    app.dataengine.mssql-feeder.mssql.password=
    app.dataengine.mssql-feeder.mssql.databasename=
    app.dataengine.mssql-feeder.mssql.authenticationscheme=
    app.dataengine.mssql-feeder.gscpercluster=1
    app.dataengine.mssql-feeder.gsc.memory=256m
    app.dataengine.mssql-feeder.gsc.create=y
    app.dataengine.mssql-feeder.sqlite.dbfile=/dbagigawork/sqlite/mssqlFeeder.db
    app.dataengine.mssql-feeder.space.name=bllspace
    app.dataengine.mssql-feeder.writeBatchSize=10000
    app.dataengine.mssql-feeder.sleepAfterWriteInMillis=500
17. Rebuild MsSqlFeeder jar from https://github.com/GigaSpaces-ProfessionalServices/TAU/tree/master/apps/MsSqlFeeder and place it to /dbagigashare/current/mssql/jars/
18. Copy load data scripts from https://github.com/GigaSpaces-ProfessionalServices/TAU/tree/master/deployment/MSSQL_FEEDER/scripts to /dbagigashare/current/mssql/scripts/
### TAU v4.23-tau-release tag
19. Update app.config with following values
    app.newspace.wantspaceproperty=y
    app.newspace.spaceproperty.filepath.target=/dbagiga/gs_config/imspace.properties
20. Update app.yaml with following values unser ".gs.config"
    imspace:
        imspacepropertyfile: imspace.properties
21. Create "imspace.properties" and copy to "/dbagigashare/current//gs/config/imspace/" directory
    space-config.engine.memory_usage.high_watermark_percentage=97
    space-config.engine.memory_usage.write_only_block_percentage=96
    space-config.engine.memory_usage.write_only_check_percentage=95
    space-config.engine.memory_usage.gc-before-shortage=false

### TAU v4.24-tau-release tag
22. Rebuild objectManagement jar from https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/objectManagement and reinstall objecmanagement service
23. Update app.yaml file add pollingFileName: pollingcontainer.txt below indexBatchFileName property
24. sample pollingcontainer.txt file :
    #typeName	srcPropName	destPropName	obfuscatePropName	obfuscationType	spaceId
    STUD.TA_HODAA	PNIMI	K_IDNO	IS_IDNO_OBFUSCATE	obfuscatToPnimi9Digits	id
    STUD.TA_PERSON	K_PNIMI	IDNO	IS_IDNO_OBFUSCATE	obfuscatToPnimi9Digits	K_PNIMI
    STUD.TA_PERSON	K_PNIMI	PASSPORT	IS_PASSPORT_OBFUSCATE	obfuscatToPnimi14Digits	K_PNIMI
### TAU v4.25-tau-release tag
25. Build data validator server and agent code from - https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/data-validator
26. Copy generated agent and server jars to /dbagigashare/current/data-validator/jars on pivot machine
27. Update host Ips in /dbagigashare/env_config/host.yaml on pivot machine
    data_validator_server :
      host1 : 172.31.47.137
    data_validator_agent :
      host1 : 172.31.41.161
      host2 : 172.31.47.193
28. Add entry if not available in app.yaml
    data-validator:
      jars:
        serverjar: data-validator-server-0.0.1-SNAPSHOT.jar
        agentjar: data-validator-agent-0.0.1-SNAPSHOT.jar
### TAU v4.26-tau-release tag
29. Re build data validator server and agent code from - https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/data-validator
30. Follow the same steps from TAU v4.25-tau-release tag section
### TAU v4.27-tau-release tag
31. Removed app.spacejar.pu.partitions property from app.config
### TAU v4.32-tau-release tag
32. Update app.yaml and add below section in parallel to mssql & oracle  :
    gilboa:
      config: null
      jars:
        gilboaJarFile: GilboaSyncFeeder-1.0-SNAPSHOT
      scripts: null
33. Update app.config file :
    app.dataengine.gilboa-feeder.sqlite.dbfile=/dbagigawork/sqlite/gilboaFeeder.db
34. Create gilboa folder under /dbagigashare/current/ with same folders as mssql 
35. Build gilboa jar from https://github.com/GigaSpaces-ProfessionalServices/TAU/releases/tag/TAU-Infra-1.0 & copy to /dbagigashare/current/gilboa/jars/
36. Sample /dbagigashare/current/gilboa/scripts/load_Portal_Calendary_Changes_View.sh :
    echo "starting Portal_Calendary_View"
    table_name="dbo.Portal_Calendary_View"
    exclude_columns=""
    pk_columns=""
    curl -XPOST "http://$1:$2/table-feed/start?table-name=${table_name}&base-column=v_timestamp"
### TAU v4.33-tau-release tag
37. Add following properties in app.config
    app.dataengine.mssql-feeder.rest.port=8302
    app.dataengine.oracle-feeder.rest.port=8501
    app.dataengine.gilboa-feeder.rest.port=8251
38. Build data validator agent code from - https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/data-validator
39. Copy generated agent jar to /dbagigashare/current/data-validator/jars on pivot machine    
40. Pull and Rebuild MsSqlFeeder jar from https://github.com/GigaSpaces-ProfessionalServices/TAU/tree/master/apps/MsSqlFeeder and place it to /dbagigashare/current/mssql/jars/
41. In mssql load scripts add param : clear-before-start=true. So sample script will look like :
    curl -XPOST "http://$1:$2/table-feed/start?table-name=${table_name}&base-column=v_timestamp&clear-before-start=true"
### TAU v4.35-tau-release tag    
42. Build data validator server and agent code from - https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/data-validator
43. Copy generated agent and server jars to /dbagigashare/current/data-validator/jars on pivot machine