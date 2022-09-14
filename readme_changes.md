1. app.config
   param added :
    app.di.base.kafka.wanttoremove=n
    app.di.base.zk.wanttoremove=n
    app.di.base.telegraf.wanttoremove=n
    app.grafana.gsconfigyaml.target=/etc/grafana/provisioning/dashboards/
    app.grafana.provisioning.dashboards.target=/usr/share/grafana/conf/provisioning/dashboards/
2. app.yaml
    grafana section updated
    grafana:
        catalog:
          jars:
            catalogjar: catalogue-service.jar
        dashboards:
        gsconfig: gs_config.yaml    