package com.gigaspaces.datavalidator.model;

public class Measurement {
    private String dataSourceType;
    private String dataSourceHostIp;
    private String dataSourcePort;
    private String username;
    private String password;
    private String schemaName;
    private String tableName;
    private String fieldName;
    private String whereCondition;

    public Measurement(String dataSourceType, String dataSourceHostIp, String dataSourcePort, String username, String password, String schemaName, String tableName, String fieldName, String whereCondition) {
        this.dataSourceType = dataSourceType;
        this.dataSourceHostIp = dataSourceHostIp;
        this.dataSourcePort = dataSourcePort;
        this.username = username;
        this.password = password;
        this.schemaName = schemaName;
        this.tableName = tableName;
        this.fieldName = fieldName;
        this.whereCondition = whereCondition;
    }

    public String getDataSourceType() {
        return dataSourceType;
    }

    public void setDataSourceType(String dataSourceType) {
        this.dataSourceType = dataSourceType;
    }

    public String getDataSourceHostIp() {
        return dataSourceHostIp;
    }

    public void setDataSourceHostIp(String dataSourceHostIp) {
        this.dataSourceHostIp = dataSourceHostIp;
    }

    public String getDataSourcePort() {
        return dataSourcePort;
    }

    public void setDataSourcePort(String dataSourcePort) {
        this.dataSourcePort = dataSourcePort;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
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
}
