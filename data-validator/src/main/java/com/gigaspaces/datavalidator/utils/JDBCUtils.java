package com.gigaspaces.datavalidator.utils;

import com.j_spaces.core.client.SQLQuery;
import com.j_spaces.jdbc.SelectQuery;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class JDBCUtils {

    static List<String> aggregation_functions = new ArrayList<String>();
    static{
        aggregation_functions.add("avg");
        aggregation_functions.add("count");
        aggregation_functions.add("min");
        aggregation_functions.add("max");
    }
    public static Connection getConnection(String dataSource, String dataSourceHostIp, String dataSourcePort, String schemaName, String username, String password) {
        Connection connection = null;
        String connectionString = "";
        try {
            switch(dataSource) {
                case "gigaspaces":
                    Class.forName("com.j_spaces.jdbc.driver.GDriver").newInstance();
                    connectionString  = "jdbc:gigaspaces:url:jini://"+dataSourceHostIp+":"+dataSourcePort+"/*/"+schemaName;
                    break;
                case "mysql":
                    Class.forName("com.mysql.jdbc.Driver").newInstance();
                    connectionString  = "jdbc:mysql://"+dataSourceHostIp+":"+dataSourcePort+"/"+schemaName+"?characterEncoding=latin1";
                    break;
                case "db2":
                    // code block
                    Class.forName("com.ibm.db2.jcc.DB2Driver").newInstance();
                    break;
                case "ms-sql":
                    // code block
                    Class.forName("com.microsoft.sqlserver.jdbc.SQLServerDriver").newInstance();
                    break;
            }
            connection = DriverManager.getConnection(connectionString,username, password);
        } catch (InstantiationException e) {
            e.printStackTrace();
        } catch (IllegalAccessException e) {
            e.printStackTrace();
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        } catch (SQLException throwables) {
            throwables.printStackTrace();
        }
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

        if(false && limitRecords != -1){
            switch(dataSource) {
                case "gigaspaces":
                    query.append(" (SELECT ").append(fieldName).append(" FROM ").append(tableName).append(" WHERE ROWNUM <= ").append(limitRecords).append(" ) A");
                    break;
                case "mysql":
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
        return query.toString();
    }
}
