package com.gigaspaces.datavalidator.db;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class DbProperties {

	@Value("${show_sql:false}")
	private boolean show_sql;
	@Value("${format_sql:false}")
	private boolean format_sql;
	@Value("${dialect:org.hibernate.dialect.SQLiteDialect}")
	private String dialect;
	@Value("${driver:org.sqlite.JDBC}")
	private String driver;
	@Value("${user:}")
	private String user;
	@Value("${pass:}")
	private String pass;
	@Value("${hbm2dll_auto:update}")
	private String hbm2dll_auto;
	@Value("${connection_url:jdbc:sqlite:}")
	private String connection_url;
	@Value("${pathToDataBase:datavalidator.db}")
	private String pathToDataBase;

	public boolean isShow_sql() {
		return show_sql;
	}

	public void setShow_sql(boolean show_sql) {
		this.show_sql = show_sql;
	}

	public boolean isFormat_sql() {
		return format_sql;
	}

	public void setFormat_sql(boolean format_sql) {
		this.format_sql = format_sql;
	}

	public String getDialect() {
		return dialect;
	}

	public void setDialect(String dialect) {
		this.dialect = dialect;
	}

	public String getDriver() {
		return driver;
	}

	public void setDriver(String driver) {
		this.driver = driver;
	}

	public String getUser() {
		user = user == null ? "" : user;
		return user;
	}

	public void setUser(String user) {
		this.user = user;
	}

	public String getPass() {
		pass = pass == null ? "" : pass;
		return pass;
	}

	public void setPass(String pass) {
		this.pass = pass;
	}

	public String getHbm2dll_auto() {
		return hbm2dll_auto;
	}

	public void setHbm2dll_auto(String hbm2dll_auto) {
		this.hbm2dll_auto = hbm2dll_auto;
	}

	public String getConnection_url() {
		connection_url = connection_url + pathToDataBase;
		return connection_url;
	}

	public void setConnection_url(String connection_url) {
		this.connection_url = connection_url;
	}

}
