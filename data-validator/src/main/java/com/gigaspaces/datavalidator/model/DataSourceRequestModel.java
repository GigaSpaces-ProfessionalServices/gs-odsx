package com.gigaspaces.datavalidator.model;

public class DataSourceRequestModel {
	private String dataSourceId;
	private String dataSourceName;
	private String dataSourceType;
	private String dataSourceHostIp;
	private String dataSourcePort;
	private String username;
	private String password;
	private String integratedSecurity;
    private String authenticationScheme;
    private String properties;
    
	public String getDataSourceId() {
		return dataSourceId;
	}

	public void setDataSourceId(String dataSourceId) {
		this.dataSourceId = dataSourceId;
	}

	public String getDataSourceName() {
		return dataSourceName;
	}

	public void setDataSourceName(String dataSourceName) {
		this.dataSourceName = dataSourceName;
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

	public String getIntegratedSecurity() {
		return integratedSecurity;
	}

	public void setIntegratedSecurity(String integratedSecurity) {
		this.integratedSecurity = integratedSecurity;
	}
	public String getAuthenticationScheme() {
		return authenticationScheme;
	}
	public void setAuthenticationScheme(String authenticationScheme) {
		this.authenticationScheme = authenticationScheme;
	}
	public String getProperties() {
		return properties;
	}
	public void setProperties(String properties) {
		this.properties = properties;
	}
	@Override
	public String toString() {
		return "DataSourceRequestModel [dataSourceId=" + dataSourceId + ", dataSourceName=" + dataSourceName
				+ ", dataSourceType=" + dataSourceType + ", dataSourceHostIp=" + dataSourceHostIp + ", dataSourcePort="
				+ dataSourcePort + ", username=" + username + ", password=" + password + ", integratedSecurity="
				+ integratedSecurity + ", authenticationScheme=" + authenticationScheme + ", properties=" + properties
				+ "]";
	}
	
	
}
