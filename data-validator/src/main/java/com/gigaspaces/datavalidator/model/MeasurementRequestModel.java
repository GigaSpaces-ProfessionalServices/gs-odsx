package com.gigaspaces.datavalidator.model;

public class MeasurementRequestModel {
    private String measurementId;
    private String dataSourceId;
    private String test;
//    private String dataSourceType;
//    private String dataSourceHostIp;
//    private String dataSourcePort;
//    private String username;
//    private String password;
    private String schemaName;
    private String tableName;
    private String fieldName;
    private String whereCondition;
//    private String integratedSecurity;
    
    public MeasurementRequestModel() {
    }
    
    

    public String getDataSourceId() {
		return dataSourceId;
	}



	public void setDataSourceId(String dataSourceId) {
		this.dataSourceId = dataSourceId;
	}



	public String getMeasurementId() {
        return measurementId;
    }

    public void setMeasurementId(String measurementId) {
        this.measurementId = measurementId;
    }

    public String getTest() {
        return test;
    }

    public void setTest(String test) {
        this.test = test;
    }

//    public String getDataSourceType() {
//        return dataSourceType;
//    }
//
//    public void setDataSourceType(String dataSourceType) {
//        this.dataSourceType = dataSourceType;
//    }
//
//    public String getDataSourceHostIp() {
//        return dataSourceHostIp;
//    }
//
//    public void setDataSourceHostIp(String dataSourceHostIp) {
//        this.dataSourceHostIp = dataSourceHostIp;
//    }
//
//    public String getDataSourcePort() {
//        return dataSourcePort;
//    }
//
//    public void setDataSourcePort(String dataSourcePort) {
//        this.dataSourcePort = dataSourcePort;
//    }
//
//    public String getUsername() {
//        return username;
//    }
//
//    public void setUsername(String username) {
//        this.username = username;
//    }
//
//    public String getPassword() {
//        return password;
//    }
//
//    public void setPassword(String password) {
//        this.password = password;
//    }

    public String getSchemaName() {
        return schemaName;
    }

    public void setSchemaName(String schemaName) {
        this.schemaName = schemaName;
    }

    public String getTableName() {
        return tableName;
    }

    public void setTableName(String tableName) {
        this.tableName = tableName;
    }

    public String getFieldName() {
        return fieldName;
    }

    public void setFieldName(String fieldName) {
        this.fieldName = fieldName;
    }

    public String getWhereCondition() {
        return whereCondition;
    }

    public void setWhereCondition(String whereCondition) {
        this.whereCondition = whereCondition;
    }

//	public String getIntegratedSecurity() {
//		return integratedSecurity;
//	}
//
//	public void setIntegratedSecurity(String integratedSecurity) {
//		this.integratedSecurity = integratedSecurity;
//	}



	@Override
	public String toString() {
		return "MeasurementRequestModel [measurementId=" + measurementId + ", dataSourceId=" + dataSourceId + ", test="
				+ test + ", schemaName=" + schemaName + ", tableName=" + tableName + ", fieldName=" + fieldName
				+ ", whereCondition=" + whereCondition +  "]";
	}
    
    
}
