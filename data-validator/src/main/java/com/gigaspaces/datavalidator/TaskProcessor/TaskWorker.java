package com.gigaspaces.datavalidator.TaskProcessor;

import java.util.concurrent.*;
import java.util.logging.Logger;

public class TaskWorker implements Runnable{
    protected Logger logger = Logger.getLogger(this.getClass().getName());
    private int numThreads;
    private static ExecutorService executor;
    private static CompletionService<TestTask> pool;

    public TaskWorker(int numThreads){
        this.numThreads = numThreads;
        executor = Executors.newFixedThreadPool(numThreads);
        pool = new ExecutorCompletionService<TestTask>(executor);
    }

    public void startworker(int numThreads){

        TestTask st = null;

        for(;;){
            st = TaskQueue.getTask();
            //logger.info("TaskWorker:: getNewTask: "+st);
            if(st != null) {
                if (System.currentTimeMillis() >= st.getTime()) {
                    String result = st.executeTask();
                    logger.info("TaskWorker:: Result: " + result);
                    CompleteTaskQueue.setTask(st);
                } else {
                    //logger.info("TaskWorker:: Adding task back to Queue");
                    TaskQueue.setTask(st);
                }
            }
            //if(st != null) pool.submit(st);
            try {
                Thread.sleep(5000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }

    public static void getTasksDone(){
        try { Thread.sleep(1000); } catch (InterruptedException e) { }
        for(;;){
            try {
                System.out.println("Looking for Complete Tasks");
                Future<TestTask> result = pool.take();
                System.out.println("Found. Trying to get the Task:"  );

                TestTask st = result.get();
                System.out.println("Task " + st.getId() + " Completed - " + st.getResult());
                CompleteTaskQueue.setTask(st);

            } catch (InterruptedException e) {
                //e.printStackTrace();
                System.out.println("Task Interrupted!");
            } catch (ExecutionException e) {
                //e.printStackTrace();
                System.out.println("Error getting the task!");
            }
        }
    }

    public void run() {
        startworker(numThreads);
    }

}
