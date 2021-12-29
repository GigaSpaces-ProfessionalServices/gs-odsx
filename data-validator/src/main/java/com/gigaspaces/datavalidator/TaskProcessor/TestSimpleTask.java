package com.gigaspaces.datavalidator.TaskProcessor;

import java.io.Serializable;
import java.util.concurrent.Callable;
import java.util.logging.Logger;

public class TestSimpleTask implements Callable<TestSimpleTask>, Serializable {
    protected Logger logger = Logger.getLogger(this.getClass().getName());
    private String id;
    private long time;
    private String result;

    public TestSimpleTask(String id, long time){
        this.id = id;
        this.time = time;
    }

    public TestSimpleTask(String id, long time, String result){
        this.id = id;
        this.time = time;
        this.result = result;
    }

    public String getId(){
        return id;
    }

    public String getResult(){
        return (result == null) ? "I didn't sleep!" : result;
    }

    public String executeTask(){
        try {
            return "Successfully executed task id: "+getId();
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public TestSimpleTask call() throws Exception {
        //System.out.println("----- Task " + id + " started -----");
        String result = executeTask();
        if(result == null){
            //System.out.println("----- Task " + id + " Interrupted -----");
            return null;
        }
        else {
            //System.out.println("----- Task " + id + " Completed -----");
            return new TestSimpleTask(id, time, result);
        }
    }

    public long getTime() {
        return time;
    }
}
