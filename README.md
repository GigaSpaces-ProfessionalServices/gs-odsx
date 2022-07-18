# <u>ODSX (Bank Leumi)</u>

### <u>Environment setup</u>
  - In AWS go to EFS -> create -> 
  - Make sure security group is same for EFS and EC2 user
  - For Pivot machine create directory structure same as app.yaml file
      - sudo mkdir -p /dbagigashare/current/gsupgrade /dbagigashare/current/gs/config/space /dbagigashare/current/gs/config/metrics /dbagigashare/current/gs/jars/space /dbagigashare/current/gs/config/license /dbagigashare/current/grafana/catalog/jars /dbagigashare/current/data-validator/files /dbagigashare/current/data-validator/jars /dbagigashare/current/gs/jars/ts /dbagigashare/current/mq-connector/adabas/jars /dbagigashare/current/mq-connector/adabas/config /dbagigashare/current/mssql/files /dbagigashare/current/mq-connector /dbagigashare/current/security/jars/cef /dbagigashare/current/gs/config/logs/ /dbagigashare/current/gs/jars /dbagigashare/current/gs/config/ts /dbagigashare/current/odsx /dbagigashare/current/mssql/jars /dbagigashare/current/mssql/scripts /dbagigashare/current/db2/jars /dbagigashare/current/db2/scripts /dbagigashare/current/cr8 /dbagigashare/current/grafana /dbagigashare/current/influx /dbagigashare/current/gs /home/ec2-user/dbagigashare/gs/config /dbagigashare/current/jdk /dbagigashare/current/kafka /dbagigashare/current/nb /dbagigashare/current/nb/applicative/ssl /dbagigashare/current/nb/management/ssl /dbagigashare/current/sqlite /dbagigashare/current/security /dbagigashare/current/unzip /dbagigashare/current/zk /dbagigashare/current/telegraf
  - Go to EFS -> created EFS -> Click on Attach copy the command and point to /dbagigashare instead of efs
  - Go to other machine create directory /dbagigashare,  install NFS and run same attach command to mount created shared directory /dbagigashare
  - Mount shared file location /dbagigashare/current in AWS with all installer servers (NFS).

### <u>ODSX Configuration setup</u>
  - Copy app.config, host.yaml, app.yaml files into /dbagigashare/current/odsx/
  - If you are on AWS EC2 then modify flag cluster.usingPemFile=True
  - Uncomment or add your pem file cluster.pemFile=
  - Security : app.setup.profile=security  if you want to do secure setup
            - For unsecure installation : app.setup.profile= (keep blank)
  - If you are on DR envirounment app.setup.env=#dr (remove #) app.setup.env=dr

### <u>ODSX Configuration security setup</u>
  - app.config : app.setup.profile=security
  - After security installation of Manager, Space servers go to /dbagiga/gigaspaces-smart-ods/config/security/security.properties Make sure below configuration is present
    - com.gs.security.security-manager.class=com.gigaspaces.security.spring.SpringSecurityManager
      spring-security-config-location=../config/security/security-config.xml
  - Go to respected scripts files and mention user / password = gs-admin (ONLY FOR AWS EC2 these changes shold not committed) 
     Example : odsx_security_servers_manager_list.py
        username = "gs-admin"#str(getUsernameByHost(managerHost,appId,safeId,objectId))
        password = "gs-admin"#str(getPasswordByHost(managerHost,appId,safeId,objectId))

### <u>ODSX Configuration new host / supporting jar setup</u>
  - To add new host Example : 2 space servers but need to add 4 then
  - host.yaml -> add entries host1,host2 ... host4 and mention the respected IP / hostname
  - app.yaml maintain the supporting jars in yaml configuration
     Example : 
     gs:
         config:
           log:
             xap_logging: xap_logging.properties
                

### <u>Installation</u>

1. Clone this project as Zip and unzip in home directory (https://github.com/GigaSpaces-ProfessionalServices/odsx-Bank-Leumi).

2. Open terminal and go to scripts folder 

   cd odsx-Bank-Leumi/scripts.

3. Run setup script using 

   ./setup.sh

### <u>Usage</u>

Go to main Project directory from terminal window (cd odsx-Bank-Leumi/) for Menu driven and cli approach

##### 1. Menu driven 

Run below will start displaying various menu options 

./odsx.py

**Snapshot Management (Menu -> Settings -> Snapshot)**

###### List

- It will show list of cluster.config backups with timestamp from configured backup directory alsong with the current version. 

###### Retention 

- Used to set time interval to take backup after every X time and also set max number of backup to take.

###### Location 

- Set location for cluster.config backups.



**Manager (Menu -> Servers -> Manager)**

###### Install

- This option will install manager and prerequisite software for running Manager (**On Remote machine**).

- This option has two mode with AirGap and without AirGap. 

- You can enable AirGap mode in config/cluster.config.

- With AirGap mode (**AirGap=true**).

  - These must be installation files must be present in /home/ubuntu/install under appropriate folders  i.e : gs, java,  unzip,  wget. 

  - Example  :

    java : /home/ubuntu/install/java/jdk-11.0.11_linux-x64_bin.deb 

    unzip : /home/ubuntu/install/unzip/unzip_6.0-26_amd64.deb 

    wget : /home/ubuntu/install/wget/wget_1.20.3-1ubuntu1_amd64.deb 

    gs  : /home/ubuntu/install/gs/gigaspaces-xap-enterprise-15.8.1.zip
    
    telegraf : wget https://dl.influxdata.com/telegraf/releases/telegraf-1.19.3-1.x86_64.rpm 

  - Install JDK from deb file with above mentioned path and configure JAVA_HOME, PATH.

  - Install unzip, wget from debfile with above mentioned path.

  - Install GS and configure path , license, GS_HOME, manager(takes from gs_installation.properties file under:set singlehostManager here:)

  

- Without AirGap mode (**AirGap = false**)

  - It will download and install JDK, unzip, wget, GS from web.

  - Configure manager, license in <GS_HOME>\bin\setenv-override.sh.

  - It will take the configurations from gs_installation.properties file.

    

- It will add the newly installed manager into cluster.config file.
- If its first manager then we are starting snapshot scheduler.

###### Start

- This option will start the manager which is installed on remote machine.
- After selecting this option it will ask for Host and User of the remote machine for remote connection.

###### Stop

- This option will stop the manager which is currently running on remote machine.
- After Selecting this option it will ask for Host and User of the remote machine for remote connection to kill the manager.

###### Restore

- This option will start manager (Remote Machine) with same setenv-overrides.sh.
- After choosing this option it will ask for Host and User of the manager installed server / instance.

###### List

- It will list out the configured manager from the cluster.config file.
- It will display Name, IP, User and ResumeMode



**Space Server (Menu -> Servers -> Space)**

###### Install

- This will install everything required to run gs on vanilla server similar to manager.
- At the end it will add the newly installed space server into cluster.config file.

###### Stop 

- This option will stop the deployed space (quience)

###### Start 

- This option will start the stopped space (unquience)



**2. CLI  driven**

- Auto complete will work when typed ./odsx **tab tab** 

- Enable verbose mode by adding -v to command (this will enable detailed logs in log file).

- Help Usage (--h/-help) is working at different levels based on commands passed.

  Eg :  

  ./odsx.py -h

  ./odsx.py settings -h

  ./odsx.py settings snapshot -h

- Below are working examples.

  Snapshot Management : 

  ./odsx.py settings snapshot --list

  ./odsx.py settings snapshot --retention --retentiontime=10 min --maxretention=10

  ./odsx.py settings snapshot --location --retentionlocation=backup

  Manager Server :

  ./odsx.py servers manager --install/start/stop/restore --host 18.223.117.241 -u ubuntu -v

  ./odsx.py servers manager --list

  Space Server : 

  ./odsx.py servers space --install/start/stop --host 18.223.117.241 -u ubuntu -v

  ./odsx.py servers space --list

  