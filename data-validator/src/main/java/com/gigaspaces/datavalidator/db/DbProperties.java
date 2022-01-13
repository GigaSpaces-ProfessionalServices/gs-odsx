package com.gigaspaces.datavalidator.db;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.Properties;

public class DbProperties {
	
	private boolean show_sql = false;
	private boolean format_sql = false;
	private String dialect;
	private String driver;
	private String user;
	private String pass;
	private String hbm2dll_auto;
	private String connection_url;
	private String pathToDataBase;

	public DbProperties() {
		
		try {
			
			File file = new File(System.getProperty("user.dir"));
			String filePath = new File(file.getCanonicalPath())
					/* .getParent() */ + System.getProperty("file.separator")
					+ "datavalidator.properties";
			System.out.println("Db properties file Path" + filePath);
			Properties properties = null;

			if (new File(filePath).exists()) {
				FileReader reader = new FileReader(filePath);
				properties = new Properties();
				properties.load(reader);
			} else {
				System.out.println("Db properties file not found " + filePath);
			}
			
			if (properties != null) {
				show_sql = Boolean.parseBoolean(properties.getProperty("show_sql"));
				format_sql = Boolean.parseBoolean(properties.getProperty("format_sql"));
				dialect = properties.getProperty("dialect");
				driver = properties.getProperty("driver");
				user = properties.getProperty("user");
				pass = properties.getProperty("pass");
				hbm2dll_auto = properties.getProperty("hbm2dll_auto");
				connection_url = properties.getProperty("connection_url");
				pathToDataBase = properties.getProperty("pathToDataBase");
			}
			
			if (dialect == null) {
				dialect = "org.hibernate.dialect.SQLiteDialect";
			}
			
			if (driver == null) {
				driver = "org.sqlite.JDBC";
			}
			
			if (connection_url == null) {
				connection_url = "jdbc:sqlite:";
			}

			if (pathToDataBase == null) {
				pathToDataBase = "datavalidator.db";
			}
			if (hbm2dll_auto == null) {
				hbm2dll_auto = "update";
			}
			connection_url = connection_url + pathToDataBase;

		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

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
		return connection_url;
	}

	public void setConnection_url(String connection_url) {
		this.connection_url = connection_url;
	}

}
