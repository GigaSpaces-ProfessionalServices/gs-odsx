package com.gigaspaces.datavalidator.utils;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

import com.gigaspaces.datavalidator.model.DataSource;
import com.gigaspaces.datavalidator.model.Measurement;

public class JDBCUtils {

    static List<String> aggregation_functions = new ArrayList<String>();
    static{
        aggregation_functions.add("avg");
        aggregation_functions.add("count");
        aggregation_functions.add("min");
        aggregation_functions.add("max");
        aggregation_functions.add("sum");
    }
    private static Logger logger = Logger.getLogger(JDBCUtils.class.getName());
    
    public static Connection getConnection(Measurement measurement)
			throws ReflectiveOperationException, ReflectiveOperationException, ClassNotFoundException, SQLException {

		DataSource dataSource = measurement.getDataSource();
		if (dataSource == null) {
			return null;
		}
		
		String dataSourceType = dataSource.getDataSourceType();
		String dataSourceHostIp = dataSource.getDataSourceHostIp();
		String dataSourcePort = dataSource.getDataSourcePort();
		String username = dataSource.getUsername();
		String password = dataSource.getPassword();
		String integratedSecurity = dataSource.getIntegratedSecurity();
		String authenticationScheme = dataSource.getAuthenticationScheme();
		String properties = dataSource.getProperties();
		String schemaName = measurement.getSchemaName();

		Connection connection = null;
		String connectionString = "";

		switch (dataSourceType) {

		case "gigaspaces":
			Class.forName("com.j_spaces.jdbc.driver.GDriver").newInstance();
			connectionString = "jdbc:gigaspaces:url:jini://" + dataSourceHostIp + ":" + dataSourcePort + "/*/"
					+ schemaName;
			break;

		case "mysql":
			Class.forName("com.mysql.cj.jdbc.Driver").newInstance();
			connectionString = "jdbc:mysql://" + dataSourceHostIp + ":" + dataSourcePort + "/" + schemaName
					+ "?zeroDateTimeBehavior=CONVERT_TO_NULL";
			break;

		case "db2":
			Class.forName("com.ibm.db2.jcc.DB2Driver").newInstance();
			connectionString = "jdbc:db2://" + dataSourceHostIp + ":" + dataSourcePort + "/" + schemaName;
			break;

		case "ms-sql":
			Class.forName("com.microsoft.sqlserver.jdbc.SQLServerDriver").newInstance();
			connectionString = "jdbc:sqlserver://" + dataSourceHostIp + ":" + dataSourcePort + ";DatabaseName="+ schemaName + ";";

			if (integratedSecurity != null && integratedSecurity.trim().length() > 0) {
				connectionString = connectionString + "integratedSecurity=" + integratedSecurity + ";";
			}
			if (authenticationScheme != null && authenticationScheme.trim().length() > 0) {
				connectionString = connectionString + "authenticationScheme=" + authenticationScheme + ";";
			}
			if (properties != null && properties.trim().length() > 0) {
				connectionString = connectionString + properties;
			}

			break;
		}
		logger.info("DataSource ConnectionString for " + dataSource + " :" + connectionString);
		connection = DriverManager.getConnection(connectionString, username, password);

		return connection;
	}
    
	
	public static Connection getConnection(String dataSource, String dataSourceHostIp, String dataSourcePort, String schemaName, String username, String password ,
			String integratedSecurity,String isKerberoseInt,String otherProperties) throws ReflectiveOperationException, ReflectiveOperationException, ClassNotFoundException, SQLException {
		Connection connection = null;
		String connectionString = "";

		switch (dataSource) {
		
		case "gigaspaces":
			Class.forName("com.j_spaces.jdbc.driver.GDriver").newInstance();
			connectionString = "jdbc:gigaspaces:url:jini://" + dataSourceHostIp + ":" + dataSourcePort + "/*/"+ schemaName;
			break;
		
		case "mysql":
			Class.forName("com.mysql.cj.jdbc.Driver").newInstance();
			connectionString = "jdbc:mysql://" + dataSourceHostIp + ":" + dataSourcePort + "/" + schemaName	+ "?zeroDateTimeBehavior=CONVERT_TO_NULL";
			break;
		
		case "db2":
			Class.forName("com.ibm.db2.jcc.DB2Driver").newInstance();
			connectionString = "jdbc:db2://" + dataSourceHostIp + ":" + dataSourcePort + "/" + schemaName;
			break;
		
		case "ms-sql":
			Class.forName("com.microsoft.sqlserver.jdbc.SQLServerDriver").newInstance();
			connectionString = "jdbc:sqlserver://" + dataSourceHostIp + ":" + dataSourcePort + ";DatabaseName="	+ schemaName+";";

			if (integratedSecurity != null && integratedSecurity.trim().length() > 0) {
				connectionString = connectionString + "integratedSecurity="+integratedSecurity+";";
			}
			if (isKerberoseInt != null && isKerberoseInt.trim().length() > 0) {
				connectionString = connectionString + "authenticationScheme="+isKerberoseInt+";";
			}
			if (otherProperties != null && otherProperties.trim().length() > 0) {
				connectionString = connectionString + otherProperties;
			}

			break;
		}
		logger.info("DataSource ConnectionString for " + dataSource + " :" + connectionString);
		connection = DriverManager.getConnection(connectionString, username, password);
	
		return connection;
	}
    public static String buildQuery(String dataSource, String fieldName
            , String function, String tableName, long limitRecords, String whereCondition){
        StringBuilder query = new StringBuilder();
        query.append("SELECT ");
        if(function != null && aggregation_functions.contains(function.toLowerCase())){
            query.append(function).append("(A.").append(fieldName).append(") ");
        }
        query.append(" FROM ");
        //use in future
        if(false && limitRecords != -1){
            switch(dataSource) {
                case "gigaspaces":
                    query.append(" (SELECT ").append(fieldName).append(" FROM ").append(tableName).append(" WHERE ROWNUM <= ").append(limitRecords).append(" ) A");
                    break;
                case "mysql":
                	 query.append(" (SELECT ").append(fieldName).append(" FROM ").append(tableName).append(" LIMIT ").append(limitRecords).append(" ) A");
                case "ms-sql":
                    query.append(" (SELECT ").append(fieldName).append(" FROM ").append(tableName).append(" LIMIT ").append(limitRecords).append(" ) A");
                    break;
                case "db2":
                    query.append(" (SELECT ").append(fieldName).append(" FROM ").append(tableName).append(" FETCH FIRST ").append(limitRecords).append(" ROWS ONLY").append(" ) A");
                    break;
            }
        }else{
            query.append(tableName).append(" A");
            if(whereCondition != null && !whereCondition.trim().equals("")){
                query.append(" WHERE ").append(whereCondition);
            }
        }
        if(dataSource.equals("db2")){
            query.append(" with ur");
        }
        return query.toString();
    }
}