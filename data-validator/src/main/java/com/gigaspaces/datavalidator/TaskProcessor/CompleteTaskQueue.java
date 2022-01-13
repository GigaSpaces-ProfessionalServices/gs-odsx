package com.gigaspaces.datavalidator.TaskProcessor;

import java.util.ArrayList;
import java.util.List;
import java.util.Queue;
import java.util.concurrent.ConcurrentLinkedQueue;

import com.gigaspaces.datavalidator.model.TestTask;

public class CompleteTaskQueue {
    private static Queue<TestTask> tasksDone;


    public CompleteTaskQueue(){
        tasksDone = new ConcurrentLinkedQueue<>();
    }

    public static void setTask(TestTask st){
        tasksDone.add(st);
    }

    public static TestTask getTask(){
        return tasksDone.poll();
    }
    public static List<TestTask> getTasks(){
        return new ArrayList<TestTask>(tasksDone);
    }
}
