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
   app.datavalidator.measurement.time=5
   app.utilities.checkmanagersync.file=/dbagiga/utils/check_manager_sync/check_manager_sync.sh
