1. app.yaml 
    1. Added
    Under gs:
            config:
                metrics:
                    metricsxml: metrics.xml.template
                space:
                    spacepropertyfile: space.properties
            jars: 
              space:
                    spacejar: space-0.1.jar
          object:
              config:
                ddlparser: tableList.txt
              jars:
                objectmanagementjar:
2. app.config
Added after : app.space.mssqlfeeder.files.target=/dbagiga/gs_config
    app.newspace.wanttocreategsc=n
    app.newspace.name=myspace
    app.newspace.createglobally=y
    app.newspace.partitions=1
    app.newspace.ha=y
    app.spacejar.creategsc=n
    app.spacejar.creategsc.specifichost=n
    app.spacejar.creategsc.gscperhost=2
    app.spacejar.creategsc.gscmemory=256m
    app.spacejar.creategsc.gsczone=bll
    app.spacejar.wantspaceproperty=n
    app.spacejar.spaceproperty.filepath.target=/dbagiga/gs_config/
    app.spacejar.space.name=bllspace
    app.spacejar.pu.name=bllservice
    app.spacejar.pu.partitions=2
    app.spacejar.pu.zone=bll
    app.spacejar.pu.backuprequired=y
    app.spacejar.pu.maxinstancepermachine=1


 