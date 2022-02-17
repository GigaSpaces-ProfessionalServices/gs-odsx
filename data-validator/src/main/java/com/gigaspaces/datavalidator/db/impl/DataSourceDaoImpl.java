package com.gigaspaces.datavalidator.db.impl;

import java.util.List;

import org.springframework.stereotype.Repository;
import com.gigaspaces.datavalidator.db.dao.DataSourceDao;
import com.gigaspaces.datavalidator.model.DataSource;
import com.gigaspaces.datavalidator.model.ModelConstant;

@Repository
public class DataSourceDaoImpl extends DAOImplAbstract<DataSource> implements DataSourceDao{

	@Override
	public List<DataSource> getActiveDataSources() {
		String sql = "from com.gigaspaces.datavalidator.model.DataSource WHERE status='" + ModelConstant.ACTIVE+"'";
		return getAll(sql);
	}

}
