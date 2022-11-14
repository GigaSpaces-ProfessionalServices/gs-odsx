1. app.yaml
In the end of the file add this part. And remove the keys from appropriate locations in app.yaml 
   env_config:
       msqslsqljdbc: SQLJDBCDriver.conf
       datavalidatorsqljdbc: SQLJDBCDriver.conf
       ldapsourcefile: ldap-security-config.xml
       datavalidatorkeytab: UTKA02E.keytab
       mssqlkeytab: udkods2.keytab
2. Create directory env_config in /dbagigashare and add below in ~/.bashrc :
   export ENV_CONFIG=/dbagigashare/env_config/