package com.gigaspaces.datavalidator.db.impl;

import java.util.List;
import org.springframework.stereotype.Repository;
import com.gigaspaces.datavalidator.db.dao.TestTaskDao;
import com.gigaspaces.datavalidator.model.TestTask;

@Repository
public class TestTaskDaoImpl extends DAOImplAbstract<TestTask> implements TestTaskDao {

	public List<TestTask> getAllPendingTask() {

		List<TestTask> testTask = getAll();
		for (TestTask odsxTask : testTask) {
			odsxTask.getResult();
		}
		return testTask;

	}

}
