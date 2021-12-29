package com.gigaspaces.datavalidator.TaskProcessor;

import com.gigaspaces.datavalidator.utils.JDBCUtils;

import java.beans.Transient;
import java.io.Serializable;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.Properties;
import java.util.concurrent.Callable;
import java.util.logging.Logger;

public class TestTask implements Serializable {
    protected static Logger logger = Logger.getLogger(TestTask.class.getName());
    private static long maxId=0;
    private long id;
    private long time;
    private Properties dbProperties;
    private String result;


    public TestTask(long id, long time, Properties dbProperties, String result){
        this.id = id;
        this.time = time;
        this.result = result;
        this.dbProperties = dbProperties;
    }

    public long getId(){
        return id;
    }

    public String getResult(){
        return (result == null) ? "pending" : result;
    }

    public String executeTask(){
        try {
            String testType=dbProperties.getProperty("testType");
            if(testType != null && testType.equals("Measure")) {
                logger.info("Executing task id: "+id);
                String test = dbProperties.getProperty("test");
                String dataSourceType = dbProperties.getProperty("dataSourceType");
                String dataSourceHostIp = dbProperties.getProperty("dataSourceHostIp");
                String dataSourcePort = dbProperties.getProperty("dataSourcePort");
                String username = dbProperties.getProperty("username");
                String password = dbProperties.getProperty("password");
                String schemaName = dbProperties.getProperty("schemaName");
                String tableName = dbProperties.getProperty("tableName");
                String fieldName = dbProperties.getProperty("fieldName");
                String limitRecords = dbProperties.getProperty("limitRecords", "-1");
                String whereCondition = dbProperties.getProperty("whereCondition","");

                Connection conn = JDBCUtils.getConnection(dataSourceType, dataSourceHostIp, dataSourcePort, schemaName, username, password);
                Statement st = conn.createStatement();
                String query = JDBCUtils.buildQuery(dataSourceType, fieldName, test, tableName
                        , Long.parseLong(limitRecords), whereCondition);
                logger.info("query: " + query);
                //st = conn.createStatement();
                ResultSet rs = st.executeQuery(query);

                String val="";
                while (rs.next()) {
                    val = rs.getString(1);
                    logger.info("val:     " + val);
                }
                this.result = String.valueOf(val);

            }else if(testType != null && testType.equals("Compare")){

                String test = dbProperties.getProperty("test");
                String limitRecords = dbProperties.getProperty("limitRecords", "-1");
                String whereCondition = dbProperties.getProperty("whereCondition","");

                String dataSource1Type = dbProperties.getProperty("dataSource1Type");
                String dataSource1HostIp = dbProperties.getProperty("dataSource1HostIp");
                String dataSource1Port = dbProperties.getProperty("dataSource1Port");
                String username1 = dbProperties.getProperty("username1");
                String password1 = dbProperties.getProperty("password1");
                String schemaName1 = dbProperties.getProperty("schemaName1");
                String tableName1 = dbProperties.getProperty("tableName1");
                String fieldName1 = dbProperties.getProperty("fieldName1");


                Connection conn1 = JDBCUtils.getConnection(dataSource1Type, dataSource1HostIp
                        , dataSource1Port, schemaName1, username1, password1);
                Statement statement1 = conn1.createStatement();
                String query1 = JDBCUtils.buildQuery(dataSource1Type, fieldName1, test, tableName1
                        , Long.parseLong(limitRecords), whereCondition);
                logger.info("query1: " + query1);
                ResultSet resultSet1 = statement1.executeQuery(query1);

                float val1 = 0;
                while (resultSet1.next()) {
                    val1 = resultSet1.getFloat(1);
                    logger.info("val1:     " + val1);
                }

                String dataSource2Type = dbProperties.getProperty("dataSource2Type");
                String dataSource2HostIp = dbProperties.getProperty("dataSource2HostIp");
                String dataSource2Port = dbProperties.getProperty("dataSource2Port");
                String username2 = dbProperties.getProperty("username2");
                String password2 = dbProperties.getProperty("password2");
                String schemaName2 = dbProperties.getProperty("schemaName2");
                String tableName2 = dbProperties.getProperty("tableName2");
                String fieldName2 = dbProperties.getProperty("fieldName2");

                Connection conn2 = JDBCUtils.getConnection(dataSource2Type, dataSource2HostIp
                        , dataSource2Port, schemaName2, username2, password2);
                Statement statement2 = conn2.createStatement();
                String query2 = JDBCUtils.buildQuery(dataSource2Type, fieldName2, test, tableName2
                        , Long.parseLong(limitRecords),whereCondition);
                logger.info("query2: " + query2);
                ResultSet resultSet2 = statement2.executeQuery(query2);

                float val2 = 0;
                while (resultSet2.next()) {
                    val2 = resultSet2.getFloat(1);
                    logger.info("val2:     " + val2);
                }
                if(val1 == val2){
                    this.result="PASS";
                }else{
                    logger.info("==> Test Result: FAIL, Test type: "+test+", DataSource1 Result: "+val1+", DataSource2 Result: "+val2);
                    this.result="FAIL";
                }
            }else{
                this.result = "Incorrect type";
            }
            return this.result;
        } catch (Exception e) {
            e.printStackTrace();
            this.result = "FAIL: "+e.getMessage();
        }
        return this.result;
    }

    public long getTime() {
        return time;
    }
    public static long getMaxId(){
        return ++maxId;
    }
    public String toString() {
        return "[" + id + " " + result+"]";
    }
}
