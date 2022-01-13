package com.gigaspaces.datavalidator.TaskProcessor;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Queue;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.PriorityBlockingQueue;
import java.util.logging.Logger;

import com.gigaspaces.datavalidator.model.TestTask;

public class TaskQueue {
	
    protected static Logger logger = Logger.getLogger(TaskQueue.class.getName());
    private static PriorityBlockingQueue<TestTask> taskQueue;


        public TaskQueue(){
            taskQueue = new PriorityBlockingQueue<TestTask>(
                    100,
                    Comparator.comparing(TestTask::getTime));
        }

        public static void setTask(TestTask st){
            taskQueue.add(st);
        }

        public static String executeTask(){
            TestTask st = taskQueue.poll();
            if (st == null) return null;
            String result = st.executeTask();
            if(result != null) return result;
            return null;
        }

        public static TestTask getTask(){
            return taskQueue.poll();
        }
        
    public static List<TestTask> getTasks(){
        return new ArrayList<TestTask>(taskQueue);
    }

}
