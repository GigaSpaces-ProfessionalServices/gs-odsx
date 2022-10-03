1. app.yaml
   Replaced from .gs.ts to 
     object.config.ddlparser.ts.bck.currentTs
     object.config.ddlparser.ts.bck.previousTs
2. Create the influxdb.conf.template at location /dbagigashare/current/influx/config/influxdb.conf.template

3. Add the code mention below.

[data]
 # The directory where the TSM storage engine stores TSM files.
 dir = "/dbagigainflaxdata/influxdb/data"
 
 # The directory where the TSM storage engine stores WAL files.
 wal-dir = "/dbagigainflaxdata/influxdb/wal"
 
 max-series-per-database = 0
