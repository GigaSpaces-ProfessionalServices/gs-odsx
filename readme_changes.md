1. setup.sh / quicksetup.sh
    - Source installer directory root
    - export ODSXARTIFACTS=/dbagigashare/current/
    - Once you change the root <current> same root needs to be change to app.yaml file
2. app.yaml 
    - Changed the structure accordingly alphabatical order a->z
    - Folder structure changed better to replace file accordingly:
       security -> jars -> cef [folder] ->CEFLogger-1.0-SNAPSHOT.jar
       security -> jars -> security jars
 3. logging.config
    - Changed logging for odsx to -> /dbagigalogs/odsx.log
 4. app.config
    - Added: 
        - app.setup.profile=security
        - app.manager.cefXapLogging.target.file
    - changed:
        - app.di.base.kafka.zk=/dbagigasoft/
    - Removed:
        - current.security.jars.cef.cefloggingjar
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
             

        
           