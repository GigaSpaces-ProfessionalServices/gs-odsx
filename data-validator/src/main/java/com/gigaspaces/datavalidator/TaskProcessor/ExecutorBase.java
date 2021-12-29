package com.gigaspaces.datavalidator.TaskProcessor;

import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import java.util.logging.Logger;

@Component
public class ExecutorBase {
    protected Logger logger = Logger.getLogger(this.getClass().getName());

    @PostConstruct
    public void atStartup() {
        TaskQueue queue = new TaskQueue();
        CompleteTaskQueue completeTaskQueue = new CompleteTaskQueue();
        Thread worker = new Thread(new TaskWorker(5));
        worker.start();
        logger.info("###### Worker startup ok");
    }
}
