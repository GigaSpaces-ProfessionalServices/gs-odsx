1. Create directory /dbagigashare/current/gs/jars/zookeeper/ and copy the new zookeeper jar files
2. Copy new zk jar names in app.yaml file as below
   gs:
     jars:
       zookeeper:
         zkjars:
           - curator-client-5.2.1.jar
           - curator-framework-5.2.1.jar
           - curator-recipes-5.2.1.jar
           - metrics-core-3.2.5.jar
           - netty-all-4.1.68.Final.jar
           - snappy-java-1.1.7.3.jar
           - xap-zookeeper.jar
           - zookeeper-3.6.3.jar
           - zookeeper-jute-3.6.3.jar
3. Configure target path in app.config file
   app.xap.newzk.jar.target=/dbagiga/gigaspaces-smart-ods/lib/platform/zookeeper/
4. Configure measurement time in app.config file
   app.dv.measurement.time=3600
   change app.kapacitor.port=9092 to app.kapacitor.port=9992
5. In KAPACITOR alerts should be in /dbagigashare/current/kapacitor/
   Templates files should in /dbagigashare/env_config/kapacitor/
   kapacitor.conf.template will reside in /dbagigashare/env_config/kapacitor/config
6. [LEUMI-537] Create folder security in /dbagigashare/env_config/ & copy files ldap-security-config.xml, SQLJDBCDriver.conf, *.keytab
7. [LEUMI-537] Update app.yaml file as below
   env_config:
     security:
       sqljdbc: SQLJDBCDriver.conf
       keytab: keytab
       ldapsourcefile: ldap-security-config.xml
8. [LEUMI-537] Copy nb folder /dbagigashare/current/nb/ to /dbagigashare/env_config/nb/management & applicative. Keep tar.gz file location as it.
