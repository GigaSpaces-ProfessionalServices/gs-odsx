1. In app.yaml file updated keytab & sql config
   env_config:
     sqljdbc: SQLJDBCDriver.conf
     keytab: UTKA02E.keytab
     ldapsourcefile: ldap-security-config.xml
2. Also the structure for object jars is now and removed retention jar from appropriate location :
   jars:
     management:
       objectmanagementjar: objectManagement.jar
     retention:
       retentionjar: retention-manager.jar
3. In app.config updated target path for data validator :
   app.dv.install.target=/dbagiga/gs_config
4. Names for tier storage jar and in memory jar are updated as tiered_storage_jar-0.1.jar and in_memory_jar-0.1.jar
