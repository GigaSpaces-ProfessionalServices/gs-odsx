package com.gigaspaces.datavalidator.db.impl;
import java.util.List;

import org.springframework.stereotype.Repository;
import com.gigaspaces.datavalidator.db.dao.MeasurementDao;
import com.gigaspaces.datavalidator.model.DataSource;
import com.gigaspaces.datavalidator.model.Measurement;
import com.gigaspaces.datavalidator.model.ModelConstant;

@Repository
public class MeasurementDaoImpl extends DAOImplAbstract<Measurement> implements MeasurementDao {

	@Override
	public List<Measurement> getActiveMeasurements() {
		String sql = "from com.gigaspaces.datavalidator.model.Measurement WHERE status='" + ModelConstant.ACTIVE+"'";
		return getAll(sql);
	}

}
