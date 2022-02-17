package com.gigaspaces.datavalidator.TaskProcessor;

import java.util.concurrent.*;
import java.util.logging.Logger;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.gigaspaces.datavalidator.db.service.TestTaskService;
import com.gigaspaces.datavalidator.model.TestTask;

@Component
public class TaskWorker implements Runnable {

	@Autowired
	private TestTaskService odsxTaskDaoService;
	
	private Logger logger = Logger.getLogger(this.getClass().getName());
	private int numThreads;
	private static ExecutorService executor;
	private static CompletionService<TestTask> pool;

	
	public void setNumThreads(int numThreads) {
		this.numThreads = numThreads;
		executor = Executors.newFixedThreadPool(numThreads);
		pool = new ExecutorCompletionService<TestTask>(executor);
	}
	
	public TaskWorker() {
	}

	public void startworker(int numThreads) {

		TestTask st = null;

		for (;;) {
			st = TaskQueue.getTask();
			if (st != null) {
				if (System.currentTimeMillis() >= st.getTime()) {
					String result = st.executeTask();
					logger.info("TaskWorker::Id:Result: " + st.getId() + ":" + result);
					odsxTaskDaoService.update(st);
					CompleteTaskQueue.setTask(st);
				} else {
					logger.info("TaskWorker:: Adding task back to Queue :" + st.getId()+" "+st.getType()+" ["+st.getMeasurementIds()+"] ");
					TaskQueue.setTask(st);
				}
			}
			try {
				Thread.sleep(5000);
			} catch (InterruptedException e) {
				e.printStackTrace();
			}
		}
	}

	public static void getTasksDone() {
		
		try {
			Thread.sleep(1000);
		} catch (InterruptedException e) {
		}
		
		for (;;) {
			try {
			
				System.out.println("Looking for Complete Tasks");
				Future<TestTask> result = pool.take();
				System.out.println("Found. Trying to get the Task:");
				TestTask st = result.get();
				System.out.println("Task " + st.getId() + " Completed - " + st.getResult());
				CompleteTaskQueue.setTask(st);

			} catch (InterruptedException e) {
				System.out.println("Task Interrupted!");
			} catch (ExecutionException e) {
				System.out.println("Error getting the task!");
			}
		}
	}

	public void run() {
		startworker(numThreads);
	}

}
