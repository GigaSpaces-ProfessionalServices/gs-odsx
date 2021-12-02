

C
III
For  Initial Setup :
--------------------
 > Untar file in home directory or download from https://github.com/GigaSpaces-ProfessionalServices/odsx-Bank-Leumi
 > cd odsx-Bank-Leumi/scripts
  This will start installing required libraries
 > ./setup.sh

1. For Menu driven
 > Go to Project Directory
 > ./odsx.py
Manager
---------
2. For Manager choose option from Main Menu
 >  [2] Servers
3. It will displays sub menus under selected- Servers option
    Choose Manager option to perform certain operation on Manager
 >  [2] Manager
4. It will displays sub menus under selected- Manager option
    Choose required options of Manager to perform.
 > [1] Restore
    - This option will start manager (Remote Machine)
    - After choosing this option it will ask for Host and User of the manager installed server / instance.
 > [2] Install
    - This option will install manager and pre-requisite software for running Manager (Remote machine).
    - This option has two mode AirGap and without AirGap
    - You can enable AirGap mode in cluster.config
    - With AirGap mode (AirGap=true)
        - There must be install folder on home i.e : /home/ubuntu/install
        - There are Folders under install  i.e : gs, java,  unzip,  wget
        - It must contain only one installation file under these folder
            java : /home/ubuntu/install/java/jdk-11.0.11_linux-x64_bin.deb
            unzip : /home/ubuntu/install/unzip/unzip_6.0-26_amd64.deb
            wget : /home/ubuntu/install/wget/wget_1.20.3-1ubuntu1_amd64.deb
            gs  : /home/ubuntu/install/gs/gigaspaces-xap-enterprise-15.8.1.zip
            1. java-|
                    |-> rpm file
                 gs-|
                    |-> <Gigaspaceversion .zip file>
              unzip-|
                    |-> rpm file
            install/gs/
            install/gs/gigaspaces-xap-enterprise-15.8.0.zip
            install/java/
            install/java/jdk-11.0.11_linux-x64_bin.rpm
            install/unzip/
            install/unzip/unzip-6.0-21.el7.x86_64.rpm

            2. Create install.tar file for these installer file keep it in install folder of odsx
               tar cvf install.tar install/
        - It will install JSK from deb file with above mentioned path and configure JAVA_HOME, PATH
        - It will install unzip from debfile with above mentioned path
        - it will install wget from deb file with above mentioened path
        - It will install GS and configure path , license, GS_HOME, manager(takes from gs_installation.properties file under:set singlehostManager here:)

    - Without AirGap mode (AirGap = false)
        - It will download and install JSK, unzip, wget, GS from web.
        - Configure manager, license in <GS_HOME>\bin\setenv-override.sh
        - It will take the configurations from gs_installation.properties file.
    - It will add the newly installed manager into cluster.config file
    - If the manager number found only one means newly added manager then it will start the scheduler.
 > [3] Start
    -  This option will start the manager which is installed on remote machine.
    -  After Selecting this option it will ask for Host and User of the remote machine for remote connection.
 > [4] Stop
    -  This option will stop the manager which is currently running on remote machine.
    -  After Selecting this option it will ask for Host and User of the remote machine for remote connection to kill the manager.
 > [6] List
    -  This option will list out the configured manager from the cluster.config file.
    -  It will display Name, IP, User and ResumeMode

FOR CLI
---------
1. Go to you home parallel to odsx.py then run command it will required host and user
2. To enable verbose mode add -v to command
3. For Install :
    > ./odsx.py servers manager install --host 18.223.117.241 -u ubuntu -v
4. For Start :
    > ./odsx.py servers manager start --host 18.223.117.241 -u ubuntu -v
5. For Start :
    > ./odsx.py servers manager stop --host 18.223.117.241 -u ubuntu -v
6. For Restore :
    > ./odsx.py servers manager restore --host 18.223.117.241 -u ubuntu -v
7. For List :
    > ./odsx.py servers manager list
