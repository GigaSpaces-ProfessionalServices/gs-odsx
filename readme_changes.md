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
