package com.gigaspaces.datavalidator.db.dao;

import java.util.List;

import org.springframework.stereotype.Repository;
import com.gigaspaces.datavalidator.model.DataSource;

@Repository
public interface DataSourceDao extends DAO<DataSource> {
	List<DataSource> getActiveDataSources();
}
