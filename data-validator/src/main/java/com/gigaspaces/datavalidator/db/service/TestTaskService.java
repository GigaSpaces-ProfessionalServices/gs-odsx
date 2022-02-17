package com.gigaspaces.datavalidator.db.service;

import java.util.ArrayList;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.gigaspaces.datavalidator.db.dao.TestTaskDao;
import com.gigaspaces.datavalidator.model.TestTask;

import com.gigaspaces.datavalidator.db.impl.TestTaskDaoImpl;
import com.gigaspaces.datavalidator.db.dao.DataSourceDao;
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
	@Autowired
	private MeasurementDao measurementDao;
	@Autowired
	private DataSourceDao dataSourceDao;
	private static String TASKRESULT_PENDING = "pending";
	
	public void add(TestTask testTask) {
		testTaskDao.add(testTask);
	}

	private void setMeasuremens(TestTask odsxTask) {
		String measurementIds = odsxTask.getMeasurementIds();
		if (measurementIds != null) {
			List<Measurement> measurementList = new ArrayList<Measurement>();
			String mIds[] = measurementIds.split(",");
			Measurement measurement=null;
			for (int index = 0; index < mIds.length; index++) {
				measurement = measurementDao.getById(Long.parseLong(mIds[index]));
				measurement.setDataSource(dataSourceDao.getById(measurement.getDataSourceId()));
				measurementList.add(measurement);
			}
			odsxTask.setMeasurementList(measurementList);
		}
	}
	
	public List<TestTask> getAllPendingTask() {
		List<TestTask> odsxTasks = getAll();
		List<TestTask> odsxTaskList = new ArrayList<TestTask>();
		for (TestTask odsxTask : odsxTasks) {
			if (TASKRESULT_PENDING.equals(odsxTask.getResult())) {
				setMeasuremens(odsxTask);
				odsxTaskList.add(odsxTask);
			}
		}
		return odsxTaskList;
	}
	
	public List<TestTask> getAllCompletedTask() {
		List<TestTask> odsxTasks = getAll();
		List<TestTask> odsxTaskList = new ArrayList<TestTask>();
		for (TestTask odsxTask : odsxTasks) {
			if (!TASKRESULT_PENDING.equals(odsxTask.getResult())) {
				setMeasuremens(odsxTask);
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

}
