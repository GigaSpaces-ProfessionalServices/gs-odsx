/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */

package com.gigaspaces.datavalidator.db.service;

import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.gigaspaces.datavalidator.db.dao.MeasurementDao;
import com.gigaspaces.datavalidator.model.Measurement;

/**
 *
 * @author alpesh
 */

@Service
public class MeasurementService {

	@Autowired
	private MeasurementDao measurementDao;

	public void add(Measurement measurement) {
		measurementDao.add(measurement);
	}
	public void deleteById(long measurementId) {
		measurementDao.deleteById(measurementId);
	}


	public long getAutoIncId() {
		return measurementDao.getAutoIncId("MEASUREMENT", "MEASUREMENT_ID");
	}

	public List<Measurement> getAll() {
		return measurementDao.getAll();
	}

	public Measurement getMeasurement(long parseLong) {
		return measurementDao.getById(parseLong);

	}

}
