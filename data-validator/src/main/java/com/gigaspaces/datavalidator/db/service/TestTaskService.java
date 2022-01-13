package com.gigaspaces.datavalidator.db.service;

import java.util.ArrayList;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.gigaspaces.datavalidator.db.dao.TestTaskDao;
import com.gigaspaces.datavalidator.model.TestTask;

import com.gigaspaces.datavalidator.db.impl.TestTaskDaoImpl;
import com.gigaspaces.datavalidator.db.dao.MeasurementDao;
import com.gigaspaces.datavalidator.db.impl.MeasurementDaoImpl;
import com.gigaspaces.datavalidator.model.Measurement;
import java.util.Map;
import java.util.HashMap;

/**
 *
 * @author alpesh
 */

@Service
public class TestTaskService {

	@Autowired
	private TestTaskDao testTaskDao;
	private static String TASKRESULT_PENDING = "pending";
	
	public void add(TestTask testTask) {
		testTaskDao.add(testTask);
	}

	public List<TestTask> getAllPendingTask() {
		List<TestTask> odsxTasks = testTaskDao.getAll();
		List<TestTask> odsxTaskList = new ArrayList<TestTask>();
		for (TestTask odsxTask : odsxTasks) {
			if (TASKRESULT_PENDING.equals(odsxTask.getResult())) {
				odsxTaskList.add(odsxTask);
			}
		}
		return odsxTaskList;
	}
	
	public List<TestTask> getAllCompletedTask() {
		List<TestTask> odsxTasks = testTaskDao.getAll();
		List<TestTask> odsxTaskList = new ArrayList<TestTask>();
		for (TestTask odsxTask : odsxTasks) {
			if (!TASKRESULT_PENDING.equals(odsxTask.getResult())) {
				odsxTaskList.add(odsxTask);
			}
		}
		return odsxTaskList;
	}
	
	public List<TestTask> getAll() {
		return testTaskDao.getAll();
	}
	
	public void update(TestTask odsxTask) {
		testTaskDao.update(odsxTask);
	}
	
	public long getAutoIncId() {  

		return testTaskDao.getAutoIncId("TESTTASK", "TESTTASK_ID");
	}
	
 //TODO: Remove Map ang get it from IDS
//	public static Map<Long, OdsxTask> odsxTaskDaoMap = new HashMap<Long, OdsxTask>();
//
//	public static Map<Long, OdsxTask> getOdsxTaskDaoMapMap() {
//		return odsxTaskDaoMap;
//	}
//
//	public static void putOdsxTaskDao(OdsxTask odsxTask) {
//		odsxTaskDaoMap.put(odsxTask.getId(), odsxTask);
//	}

}
