package com.gigaspaces.datavalidator.db.service;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.gigaspaces.datavalidator.db.dao.DataSourceDao;
import com.gigaspaces.datavalidator.model.DataSource;


@Service
public class DataSourceService {

	@Autowired
	private DataSourceDao dataSourceDao;

	public void update(DataSource dataSource) {
		dataSourceDao.update(dataSource);
	}

	public void add(DataSource dataSource) {
		dataSourceDao.add(dataSource);
	}

	public void deleteById(long dataSourceId) {
		dataSourceDao.deleteById(dataSourceId);
	}

	public long getAutoIncId() {
		return dataSourceDao.getAutoIncId("DATASOURCE", "DATASOURCE_ID");
	}

	public List<DataSource> getActiveDataSources() {
		return dataSourceDao.getActiveDataSources();
	}
	
	public List<DataSource> getAll() {
		return dataSourceDao.getAll();
	}

	public DataSource getDataSource(long parseLong) {
		return dataSourceDao.getById(parseLong);
	}

}
