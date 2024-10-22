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
### TAU v4.36-tau-release tag & TAU v4.35-tau-release tag    
42. Build data validator server and agent code from - https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/data-validator
43. Copy generated agent and server jars to /dbagigashare/current/data-validator/jars on pivot machine
44. Add following properties in app.config
    app.dv.influxdbname=telegraf
    app.dv.influxdbport=8086
    app.dv.influxdbusername=admin
    app.dv.influxdbpassword=admin
45. Replaced suffix with csv in app.yaml file
    indexBatchFileName: batchIndexes.csv    
### TAU v4.38-tau-release tag  
46. Build data validator server and agent code from - https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/data-validator
47. Copy generated agent and server jars to /dbagigashare/current/data-validator/jars on pivot machine
### TAU v4.42-tau-release tag
48. For DI zookeeper config added below properties in app.config file
    app.di.base.zk.clientPort=2181
    app.di.base.zk.initLimit=1000
    app.di.base.zk.syncLimit=1000
    app.di.base.zk.tickTime=2000
49. Make sure di-flink-taskmanager.service & di-flink-jobmanager.service are located in folder /dbagigashare/current/data-integration/di-flink/
### TAU v4.43-tau-release tag
50. Verify app.config has dataengine for secured env
    app.security.menu=manager,space,tieredstorage,feeder,mq,object,dataengine
51. Rebuild objectManagement jar from https://github.com/GigaSpaces-ProfessionalServices/TAU/tree/master/apps/objectManagement/src/main/java/com/gigaspaces/objectManagement and reinstall objecmanagement service
52. Add below section in app.yaml under security & copy the jars in current/security/jars folder
    security:
      jars:
        springconfig: spring-security-config-5.6.2.jar
        springcore: spring-security-core-5.6.2.jar
        springcrypto: spring-security-crypto-5.6.2.jar
        springweb: spring-security-web-5.6.2.jar
        xapsecurity: xap-security.jar
53. Add ldappropertysourcefile below ldapsourcefile under env_config
    ldappropertysourcefile: security.properties
54. Configure manager user and password in app.config file :
    app.manager.security.username=
    app.manager.security.password=
### TAU v4.44-tau-release tag
55. Add below section in app.yaml after oracle. Make folder under current notifier/jars and copy this jar files 
   notifier:
      config: null
      jars:
        notifierPersonalJarFile: Personal_Message_Notifier-0.4-jar-with-dependencies.jar
        notifierMessageJarFile: Group_Message_Notifier-0.7-jar-with-dependencies.jar
56. Add following properties in app.config
    app.dataengine.notifier.gsc.memory=256m
    app.dataengine.notifier.gsc.create=y
    app.dataengine.notifier.gscpercluster=1
    app.dataengine.notifier.space.name=dih-tau-space
### TAU v4.45-tau-release tag
57. Change following property value in app.config
    app.dv.install.target=/dbagiga/datavalidator
58. Re-Build data validator server and agent code from - https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/data-validator
59. Copy generated agent and server jars to /dbagigashare/current/data-validator/jars on pivot machine
### TAU v4.47-tau-release tag
60. Re-Build data validator server and agent code from - https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/data-validator
61. Copy generated agent and server jars to /dbagigashare/current/data-validator/jars on pivot machine
62. Changes in host.yaml
    Change host ip for data_validator_server and data_validator_agent
    Remove second dv agent host line if you want to run 1:1 server:agent topology
63. Changes in cluster.config
    Remove second dv agent node if you want to run 1:1 server:agent topology
64. Changes in app.config
    app.dv.server.log=/dbagigalogs/datavalidatorserver.log
    app.dv.agent.log=/dbagigalogs/datavalidatoragent.log
    app.dv.server.install.target=/dbagiga/datavalidator/server
    app.dv.agent.install.target=/dbagiga/datavalidator/agent
### TAU v4.48-tau-release tag
65. Re-Build data validator agent code from - https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/data-validator
66. Copy generated agent jars to /dbagigashare/current/data-validator/jars on pivot machine
67. Add following properties in app.config
    app.dv.server.log.level=INFO
    app.dv.agent.log.level=INFO
### TAU v4.49-tau-release tag
68. Add following properties in app.config
    odsx.utilities.scripts.folder=/giga/utils
### TAU v4.50-tau-release tag
69. Re-Build data validator server and agent code from - https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/data-validator
70. Copy generated agent and server jars to /dbagigashare/current/data-validator/jars
### TAU v4.51-tau-release tag
71. Re-Build data validator server and agent code from - https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/data-validator
72. Copy generated agent and server jars to /dbagigashare/current/data-validator/jars 
73. Update table properties to add index for optimize max calculation for gigaspace data sources
    Go to /dbagigashare/current/object/config/ddlparser
    Add following to each <table_name>.properties for which max measurement will be created
     index=T_IDKUN  (Here 'T_IDKUN' is the property name for which max value needs to be compare in data validation 
     indexType=ORDERED,EQUAL
### TAU v4.52-tau-release tag
74. Update app.yaml above telegraf section :
    security:
      jars:
        all: "*"
75. In env_config section in app.yaml update as below :
    env_config:
      security:
        conf:
          - "*.xml"
          - "*.jks"
          - "*.properties"
### TAU v4.53-tau-release tag
76. Re-Build data validator server and agent code from - https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/data-validator
77. Copy generated agent and server jars to /dbagigashare/current/data-validator/jars
### TAU v4.54-tau-vault-release tag
78. Add below in app.config, change paths as required
    app.vault.jar.location=/dbagigashare/current/gs/jars/gs-vault-1.0-SNAPSHOT-jar-with-dependencies.jar
    app.vault.db.location=/dbagigawork/sqlite/
    app.manager.workDir=/dbagigawork/
    app.space.workDir=/dbagigadata/
79. Update property app.config (this property value will be used to fetch password from vault) : 
    app.manager.security.password=manager_pass
80. Initialize vault by running below in pivot. Replace ORIGINAL_PASSWORD_TO_ENCRYPT_IN_VAULT with password :
    java -Dapp.db.path=/dbagigawork/sqlite/ -jar /dbagigashare/current/gs/jars/gs-vault-1.0-SNAPSHOT-jar-with-dependencies.jar --init
    java -Dapp.db.path=/dbagigawork/sqlite/ -jar /dbagigashare/current/gs/jars/gs-vault-1.0-SNAPSHOT-jar-with-dependencies.jar --set manager_pass=<ORIGINAL_PASSWORD_TO_ENCRYPT_IN_VAULT>
### TAU v4.60-tau-vault-release tag
81. Add/ update below flags
    app.manager.security.password=gs-admin    # set original password of manager server
    app.manager.security.password.vault=manager_pass       # property used in vault to fetch password
    app.vault.use=true    # set to true if use vault 
82. Rebuilt the jar https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/objectManagement
83. Note whenever app.vault.use flag is changed reinstall manager, space servers, object management service
### TAU v4.57-tau-release tag
84. Remove below from app.confg
    app.manager.cefLogging.jar.target=/dbagiga/gigaspaces-smart-ods/lib/required/
    app.manager.cefLogging.jar.target2=/dbagiga/gs_jars/CEFLogger-1.0-SNAPSHOT.jar
    app.manager.cefXapLogging.target.file=/../../dbagiga/gs_config/xap_logging.properties
    app.space.cefLogging.jar.target=/dbagiga/gigaspaces-smart-ods/lib/required/
85. Add below from app.confg  
    app.cefLogging.jar.target=/dbagiga/gigaspaces-smart-ods/lib/required/
86. In app.yaml add below in parallel to zookeeper in gs section:
    cef:
      cefjar: CEFLogger-1.0-SNAPSHOT.jar
### TAU v4.58-tau-release tag
87. Re-Build common, data validator server and agent code from - https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau
88. Copy generated agent and server jars to /dbagigashare/current/data-validator/jars
### TAU v4.63-tau-release tag
89. Add below in app.config file
    app.iidr.username=admin
    app.iidr.password=admin11
    app.iidrkafka.username=tsuser
    app.iidrkafka.password=tsuser11
    app.iidr-kafka.user-exit.properties.file.read-path=/giga/iidr/kafka/instance/KAFKA/conf
    app.iidr-kafka.user-exit.properties.file.write-path=/giga/iidr/kafka/instance/KAFKA/conf
89. In host.yaml file add below after dataIntegration section
    iidrdataIntegration :
       host1 : 10.0.0.5
90. In cluster.config file add below after dataIntegration section
    "iidrdataIntegration": {
        "nodes": [
        ]
    }
91. In /dbagigashare/current/data-integration/di-flink/ make sure following jar exist :
    flink-connector-kafka-1.17.0.jar
    kafka-clients-3.2.3.jar
    flink-connector-jdbc-3.1.0-1.17.jar
    flink-sql-connector-kafka-1.17.0.jar
    postgresql-42.5.4.jar
### TAU v4.64-tau-release tag
92. Adding flag for controlling objectmanagent for vault
    app.vault.objectmanagement.use=false
93. Rebuilt the jar https://github.com/GigaSpaces-ProfessionalServices/CSM-Magic-Tools/tree/tau/objectManagement
### TAU v4.67-tau-release tag
94. In app.yaml remove full zookeeper: section
95. In app.config remove app.xap.newzk.jar.target
### TAU v4.68-tau-release tag
96. In app.config added new properties and set values accordingly
    app.dataengine.apiPushUri=
    app.dataengine.apiPushXClientID=
98. Updated jar version in app.yaml as mentioned:
    notifierPersonalJarFile: Personal_Message_Notifier-0.5-jar-with-dependencies.jar
    notifierMessageJarFile: Group_Message_Notifier-0.8-jar-with-dependencies.jar
### TAU v4.70-tau-release tag 
99. Add below in app.config file
    app.dataengine.mssql-feeder.mssql.loginTimeout=20
    app.dataengine.mssql-feeder.mssql.queryTimeOut=300
### TAU v4.74-tau-release tag
100. Add below in app.config file
    app.cdc.ashost=10.0.1.129
    app.cdc.ashostport=10101