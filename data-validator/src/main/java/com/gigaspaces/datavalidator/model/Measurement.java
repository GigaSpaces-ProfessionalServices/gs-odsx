package com.gigaspaces.datavalidator.model;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;

public class Measurement implements Serializable {

	public Measurement() {

	}

	private long id;
	private long dataSourceId;
	private String type;
//	private String dataSourceType;
//	private String dataSourceHostIp;
//	private String dataSourcePort;
//	private String username;
//	private String password;
	private String schemaName;
	private String tableName;
	private String fieldName;
	private String limitRecords;
	private String whereCondition;
//	private String integratedSecurity;
	private static long maxId = 0;
	private DataSource dataSource ;
	private String status;
	
	public DataSource getDataSource() {
		return dataSource;
	}

	public void setDataSource(DataSource dataSource) {
		this.dataSource = dataSource;
	}

	public long getDataSourceId() {
		return dataSourceId;
	}

	public void setDataSourceId(long dataSourceId) {
		this.dataSourceId = dataSourceId;
	}

	public Measurement(long id, long dataSourceId,
			 String type,  String schemaName, String tableName, String fieldName, String limitRecords,
			String whereCondition) {
		this.id = id;
		this.dataSourceId = dataSourceId;
		this.type = type;
		this.schemaName = schemaName;
		this.tableName = tableName;
		this.fieldName = fieldName;
		this.whereCondition = whereCondition;
		this.limitRecords = limitRecords;
//		this.integratedSecurity = integratedSecurity;
	}

	public Measurement(long id, String type, String dataSourceType, String dataSourceHostIp, String dataSourcePort,
			String username, String password, String schemaName, String tableName, String fieldName,
			String limitRecords, String whereCondition) {
		this.id = id;
		this.type = type;
		this.schemaName = schemaName;
		this.tableName = tableName;
		this.fieldName = fieldName;
		this.whereCondition = whereCondition;
		this.limitRecords = limitRecords;
	}
	

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

    public long getId() {
        return id;
    }

    public void setId(long id) {
        this.id = id;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getLimitRecords() {
        return limitRecords;
    }

    public void setLimitRecords(String limitRecords) {
        this.limitRecords = limitRecords;
    }

//	public String getIntegratedSecurity() {
//		return integratedSecurity;
//	}
//
//	public void setIntegratedSecurity(String integratedSecurity) {
//		this.integratedSecurity = integratedSecurity;
//	}

	public static long getMaxId() {
		return ++maxId;
	}

	public String getStatus() {
		return status;
	}

	public void setStatus(String status) {
		this.status = status;
	}
	
}
