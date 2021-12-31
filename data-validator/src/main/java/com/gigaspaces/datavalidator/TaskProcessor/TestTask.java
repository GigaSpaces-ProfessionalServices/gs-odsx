package com.gigaspaces.datavalidator.TaskProcessor;

import com.gigaspaces.datavalidator.model.Measurement;
import com.gigaspaces.datavalidator.utils.JDBCUtils;

import java.io.Serializable;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.List;
import java.util.logging.Logger;

public class TestTask implements Serializable {
    protected static Logger logger = Logger.getLogger(TestTask.class.getName());
    private static long maxId=0;
    private long id;
    private long time;
    private String type;
    private List<Measurement> measurementList;
    private String result;


    public TestTask(long id, long time, String type, List<Measurement> measurementList){
        this.id = id;
        this.time = time;
        this.type= type;
        this.measurementList = measurementList;
        this.result = "pending";
    }

    public long getId(){
        return id;
    }

    public String getResult(){
        return (result == null) ? "pending" : result;
    }

    public String executeTask(){
        try {
            String testType=this.type;//dbProperties.getProperty("testType");
            if(testType != null && testType.equals("Measure")) {
                Measurement measurement = measurementList.get(0);
                logger.info("Executing task id: "+id);
                String whereCondition = measurement.getWhereCondition()!=null?measurement.getWhereCondition():"";

                Connection conn = JDBCUtils.getConnection(measurement.getDataSourceType()
                        , measurement.getDataSourceHostIp(),measurement.getDataSourcePort()
                        , measurement.getSchemaName(), measurement.getUsername(), measurement.getPassword());
                Statement st = conn.createStatement();
                String query = JDBCUtils.buildQuery(measurement.getDataSourceType(), measurement.getFieldName()
                        , measurement.getType(), measurement.getTableName()
                        , Long.parseLong(measurement.getLimitRecords()), whereCondition);
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

                Measurement measurement1 = measurementList.get(0);
                String test = measurement1.getType();
                String limitRecords=measurement1.getLimitRecords();
                String whereCondition=measurement1.getWhereCondition();

               Connection conn1 = JDBCUtils.getConnection(measurement1.getDataSourceType()
                        , measurement1.getDataSourceHostIp(),measurement1.getDataSourcePort()
                        , measurement1.getSchemaName(), measurement1.getUsername(), measurement1.getPassword());

                Statement statement1 = conn1.createStatement();
                String query1 = JDBCUtils.buildQuery(measurement1.getDataSourceType()
                        , measurement1.getFieldName(), test, measurement1.getTableName()
                        , Long.parseLong(limitRecords), whereCondition);
                logger.info("query1: " + query1);
                ResultSet resultSet1 = statement1.executeQuery(query1);

                float val1 = 0;
                while (resultSet1.next()) {
                    val1 = resultSet1.getFloat(1);
                    logger.info("val1:     " + val1);
                }

                Measurement measurement2 = measurementList.get(1);
                Connection conn2 = JDBCUtils.getConnection(measurement2.getDataSourceType()
                        , measurement2.getDataSourceHostIp(),measurement2.getDataSourcePort()
                        , measurement2.getSchemaName(), measurement2.getUsername(), measurement2.getPassword());

                Statement statement2 = conn2.createStatement();
                String query2 = JDBCUtils.buildQuery(measurement2.getDataSourceType()
                        , measurement2.getFieldName(), test, measurement2.getTableName()
                        , Long.parseLong(limitRecords), whereCondition);
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
            this.result = "FAIL: Error please refer log file";
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
