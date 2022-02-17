package com.gigaspaces.datavalidator.db.dao;

import java.util.List;

import org.springframework.stereotype.Repository;
import com.gigaspaces.datavalidator.model.Measurement;

@Repository
public interface MeasurementDao extends DAO<Measurement> {
	List<Measurement> getActiveMeasurements();
}
