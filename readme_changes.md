1. setup.sh / quicksetup.sh
    - Source installer directory root
    - export ODSXARTIFACTS=/dbagigashare/current/
    - Once you change the root <current> same root needs to be change to app.yaml file
2. app.yaml 
    - Changed the structure accordingly alphabatical order a->z
    - Folder structure changed better to replace file accordingly:
       security -> jars -> cef [folder] ->CEFLogger-1.0-SNAPSHOT.jar
       security -> jars -> security jars
    - DataValidator section added
    - grafana section added
 3. logging.config
    - Changed logging for odsx to -> /dbagigalogs/odsx.log
 4. app.config
    - Added:
        For security menu items keep 
            - app.setup.profile=security
            - app.security.menu=manager,space,tieredstorage,feeder,mq
        For enable DR env 
            - app.setup.env=dr  cuurently checked in as #dr to avoid 
        For Non security
            - app.setup.profile=
        - app.manager.cefXapLogging.target.file
        - app.dv.server.db
        - app.dv.server.log
        - app.dv.install.target
    - changed:
        - app.dataengine.db2-feeder.writeBatchSize=4000
        - app.di.base.kafka.zk=/dbagigasoft/
        - Dcom.gs.manager.leader-election.zookeeper.session-timeout=60000 to -Dcom.gs.manager.leader-election.zookeeper.session-timeout=60000
    - Removed:
        - app.space.jar.sourceFolder=/dbagiga
        - app.server.di.env=source /home/dbsh/setenv.sh;
        - app.manager.cefXapLogging.source.file
        - app.manager.source.directory.jarfiles
        - app.space.property.filePath
        - app.space.property.filepathbackup
        - app.space.db2feeder.jar.db2jcc-4.26.14.jar
        - app.space.db2feeder.jar.db2jcc_license_cu-4.16.53.jar
        - app.manager.security.spring.ldap.core.jar
        - app.manager.security.spring.ldap.jar
        - app.manager.security.spring.vaultSupport.jar
        - app.manager.security.spring.javaPassword.jar
        - app.manager.security.config.ldap.source.file
        - app.manager.cefXapLogging.source.file
        - app.manager.source.directory.jarfiles
        - app.space.mssqlfeeder.files.source
        - app.dataengine.mq.adabas.jar
        - app.dataengine.mq.keystore.file.source
        - app.dataengine.mq.kafkaconnector.jar
        - app.dataengine.db2-feeder.jar
        - app.dataengine.db2-feeder.filePath.shFile
        - app.dataengine.mssql-feeder.jar
        - app.dataengine.mssql-feeder.filePath.shFile
        - app.tieredstorage.pu.filepath
        - app.tieredstorage.criteria.filepath
        - app.tieredstorage.criteria.filepathbackup.curr
        - app.tieredstorage.criteria.filepathbackup.prev
        - app.consumer.group.pu.filepath
        
5. nb.conf
  - Makesure 
    - rename config/nb.conf to /dbagigashare/current/nb/applicative/nb.conf.template
        - This file dont contain the configurations of 
           -  GRIDUI_SERVERS=""
           -  OPSMANAGER_SERVERS=""
           -  GRAFANA_SERVERS="" 
    - rename config/nb.conf to /dbagigashare/current/nb/applicative/nb.conf.template
           - For management required above three
5. config/host.yaml
  - Removed Data Engine nodes section from host.yaml file because same installation as Data Integration
  - Added Pivot host  
  - Added Data-Validation - Servers / aget 
6. For Pivot machine create directory structure same as app.yaml file
  - sudo mkdir -p /dbagigashare/current/grafana/catalog/jars /dbagigashare/current/data-validator/files /dbagigashare/current/data-validator/jars /dbagigashare/current/gs/jars/ts /dbagigashare/current/mq-connector/adabas/jars /dbagigashare/current/mq-connector/adabas/config /dbagigashare/current/mssql/files /dbagigashare/current/mq-connector /dbagigashare/current/security/jars/cef /dbagigashare/current/gs/config/logs/ /dbagigashare/current/gs/jars /dbagigashare/current/gs/config/ts /dbagigashare/current/odsx /dbagigashare/current/mssql/jars /dbagigashare/current/mssql/scripts /dbagigashare/current/db2/jars /dbagigashare/current/db2/scripts /dbagigashare/current/cr8 /dbagigashare/current/grafana /dbagigashare/current/influxdb /dbagigashare/current/gs /home/ec2-user/dbagigashare/gs/config /dbagigashare/current/jdk /dbagigashare/current/kafka /dbagigashare/current/nb /dbagigashare/current/nb/applicative/ssl /dbagigashare/current/nb/management/ssl /dbagigashare/current/sqlite /dbagigashare/current/security /dbagigashare/current/unzip /dbagigashare/current/zk /dbagigashare/current/telegraf
  
