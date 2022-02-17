package com.gigaspaces.datavalidator.model;


import com.gigaspaces.datavalidator.utils.JDBCUtils;
import java.io.Serializable;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.List;
import java.util.logging.Logger;

public class TestTask  implements Serializable  {

	private static Logger logger = Logger.getLogger(TestTask.class.getName());

	private long id;
	private long time;
	private String type;
	private String result = null;
	private String measurementIds;
	private String errorSummary;
	private List<Measurement> measurementList;

	public TestTask() {
	System.out.print(" Constructor Call ");
	}

	public TestTask(long id, long time, String type, List<Measurement> measurementList) {

		this.id = id;
		this.time = time;
		this.type = type;
		this.measurementList = measurementList;
		this.result = "pending";

		String measurementIds = null;

		for (int index = 0; index < measurementList.size(); index++) {

			Measurement measurement = measurementList.get(index);

			if (measurement != null) {

				if (index == 0) {
					measurementIds = measurement.getId() + "";
				} else {
					measurementIds = measurementIds + "," + measurement.getId();
				}

			}

		}

		this.measurementIds = measurementIds;

	}



	public String executeTask() {

		String testType = this.type;
		Measurement measurement1 = null;
		Measurement measurement2 = null;
		
		try {
		
			if (testType != null && testType.equals("Measure")) {
			
				Measurement measurement = measurementList.get(0);
				if (measurement != null) {
					DataSource dataSource = measurement.getDataSource();
					logger.info("Executing task id: " + id);
					String whereCondition = measurement.getWhereCondition() != null ? measurement.getWhereCondition()
							: "";

					Connection conn = JDBCUtils.getConnection(measurement);
					Statement st = conn.createStatement();
					String query = JDBCUtils.buildQuery(dataSource.getDataSourceType(), measurement.getFieldName(),
							measurement.getType(), measurement.getTableName(),
							Long.parseLong(measurement.getLimitRecords()), whereCondition);
					logger.info("query: " + query);
					// st = conn.createStatement();
					ResultSet rs = st.executeQuery(query);

					String val = "";
					while (rs.next()) {
						val = rs.getString(1);
						logger.info("val:     " + val);
					}
					this.result = String.valueOf(val);
				} else {
					this.result = "FAIL: Absent of mesurement 1"; 
				}
			} else if (testType != null && testType.equals("Compare")) {

				measurement1 = measurementList.get(0);
				measurement2 = measurementList.get(1);
		
				if (measurement1 != null && measurement2 != null) {
					DataSource dataSource1 = measurement1.getDataSource();
					DataSource dataSource2 = measurement2.getDataSource();
					String test1 = measurement1.getType();
					String test2 = measurement2.getType();
					String limitRecords = measurement1.getLimitRecords();
					String whereCondition = measurement1.getWhereCondition();

					Connection conn1 = JDBCUtils.getConnection(measurement1);

					Statement statement1 = conn1.createStatement();
					String query1 = JDBCUtils.buildQuery(dataSource1.getDataSourceType(), measurement1.getFieldName(),
							test1, measurement1.getTableName(), Long.parseLong(limitRecords), whereCondition);
					logger.info("query1: " + query1);
					ResultSet resultSet1 = statement1.executeQuery(query1);

					float val1 = 0;
					while (resultSet1.next()) {
						val1 = resultSet1.getFloat(1);
						logger.info("val1:     " + val1);
					}

					Connection conn2 = JDBCUtils.getConnection(measurement2);

					Statement statement2 = conn2.createStatement();
					String query2 = JDBCUtils.buildQuery(dataSource2.getDataSourceType(), measurement2.getFieldName(),
							test2, measurement2.getTableName(), Long.parseLong(limitRecords), whereCondition);
					logger.info("query2: " + query2);
					ResultSet resultSet2 = statement2.executeQuery(query2);

					float val2 = 0;
					while (resultSet2.next()) {
						val2 = resultSet2.getFloat(1);
						logger.info("val2:     " + val2);
					}
					if (val1 == val2) {
						this.result = "PASS";
					} else {
						logger.info("==> Test Result: FAIL, Test type: " + test1 + ", DataSource1 Result: " + val1
								+ ", DataSource2 Result: " + val2);
						this.result = "FAIL";
					}
				}
			} else {
				
				this.result = "Incorrect type";
			
			}

		} catch (Exception e) {
			e.printStackTrace();
			logger.info(e.getMessage());
			this.errorSummary = e.getMessage();
			this.result = "FAIL: Error please refer log file";
			return this.result;
		}
		if (measurement1 == null || measurement2 == null) {
			if ((testType != null && testType.equals("Compare"))) {
				this.errorSummary = "Invalid input for mesurements ";
				this.result = "FAIL: Absent of mesurements 1 and 2";
			}
		}

		return this.result;
	}

	

	public String getResult() {
		return (result == null) ? "pending" : result;
	}

	public void setResult(String result) {
		this.result = result;
	}

	public long getTime() {
		return time;
	}

	public void setTime(long time) {
		this.time = time;
	}

	public String toString() {
		return "[" + id + " " + result + "]";
	}

	public String getType() {
		return type;
	}

	public void setType(String type) {
		this.type = type;
	}

	public List<Measurement> getMeasurementList() {
		return measurementList;
	}

	public void setMeasurementList(List<Measurement> measurementList) {
		this.measurementList = measurementList;
	}

	public String getMeasurementIds() {
		return measurementIds;
	}

	public void setMeasurementIds(String measurementIds) {
		this.measurementIds = measurementIds;
	}

	public String getErrorSummary() {
		return errorSummary;
	}

	public void setErrorSummary(String errorSummary) {
		this.errorSummary = errorSummary;
	}

	public long getId() {
		return id;
	}

	public void setId(long id) {
		this.id = id;
	}

}