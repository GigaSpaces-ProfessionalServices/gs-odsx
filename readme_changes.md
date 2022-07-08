1. app.yaml 
    1. Added
    Under gs:
            jars:
                  retention:
                    retentionjar: retention-manager.jar
    
2. app.config
Added:
    app.retentionmanager.sqlite.dbfile=/dbagigawork/sqlite/retention-manager.db
    # ONLY one of app.retentionmanager.scheduler.interval or app.retentionmanager.scheduler.time should be present
    app.retentionmanager.scheduler.interval=
    app.retentionmanager.scheduler.time=
    app.retentionmanager.space=bllspace

 