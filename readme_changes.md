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
3. Add this in app.config
   app.grafana.provisioning.dashboards.target=/usr/share/grafana/conf/provisioning/dashboards/
   app.utilities.recovery.monitor.space.name=bllspace
   app.utilities.gcexplicit.file=/dbagiga/utils/jcmd_exec.sh
   app.utilities.recoverymonitor.file=/dbagiga/utils/recovery_monitor/recovery_monitor.py
