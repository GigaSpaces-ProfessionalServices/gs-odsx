package com.gigaspaces.datavalidator.utils;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class JDBCUtils {
    static{

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
}
