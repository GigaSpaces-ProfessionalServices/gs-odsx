1 app.config
  app.space.start.gsc.path=/dbagigashare/current/gs/config/scripts
2. app.yaml
   utilities:
   check_manager_sync-sh: check_manager_sync.sh
   check_manager_sync-conf: check_manager_sync.conf
3. Add check_manager_sync.sh, check_manager_sync.conf file in /dbagigashare/current/utilities location in odsx.
4. create the file name start_gsc.sh on /dbagigashare/current/gs/config/scripts location in pivot machine odsx.

**content of file**

   sleep 5
   while [[ ! "$(pgrep -f 'java.*services=GSA')" ]] ; do sleep 1 ; done
   gsa_pid=$(pgrep -f 'java.*services=GSA')
   while [[ ! "$(ls -1 /dbagigalogs/*gsa-*${gsa_pid}.log 2>/dev/null)" ]] ; do sleep 1 ; done
   gsa_log=$(ls /dbagigalogs/*gsa-*${gsa_pid}.log)
   _ODS_MNG=( $(grep '^export *GS_MANAGER_SERVERS' /dbagiga/gigaspaces-smart-ods/bin/setenv-overrides.sh|awk -F= '{print $2}'|tr ',' ' ') )
   manager_not_found=0
   while [[ $manager_not_found ]] ; do
   for m in ${_ODS_MNG[@]} ; do
   [[ "$(grep "GSA discovered ServiceID.*${m}" ${gsa_log})" ]] && { manager_not_found=1 ; break ; }
   done
   [[ $manager_not_found -ne 0 ]] && break
   done

5. Updated keytab value
   keytab: keytab
6. Added flink config in app.config file (LEUMI-456)
   app.di.flink.taskmanager.memory.process.size=4000m
   app.di.flink.jobmanager.memory.jvm-metaspace.size=1500m
7. app.config
   app.di.flink.dim.mdm.install1b.confirm=n
