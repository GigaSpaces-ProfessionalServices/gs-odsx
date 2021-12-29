package com.gigaspaces.datavalidator.controller;

import com.fasterxml.jackson.databind.annotation.JsonAppend;
import com.gigaspaces.datavalidator.TaskProcessor.CompleteTaskQueue;
import com.gigaspaces.datavalidator.TaskProcessor.TaskQueue;
import com.gigaspaces.datavalidator.TaskProcessor.TestTask;
import com.gigaspaces.datavalidator.utils.JDBCUtils;
import com.google.gson.Gson;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.sql.*;
import java.util.*;
import java.util.logging.Logger;

@RestController
public class ValidateController {

    protected Logger logger = Logger.getLogger(this.getClass().getName());

    @GetMapping("/avg/{schemaName}/{tableName}/{fieldName}")
    public Double getAverageData(@PathVariable String schemaName,@PathVariable String tableName,@PathVariable String fieldName) {
        Connection conn;
        try {
            conn = JDBCUtils.getConnection("gigaspaces","localhost","4174",schemaName,"","");
            Statement st = conn.createStatement();
            String query = "SELECT AVG("+fieldName+") " + "FROM "+tableName;
            logger.info("query: "+query);
            st = conn.createStatement();
            ResultSet rs = st.executeQuery(query);
            while (rs.next()) {
                float avg = rs.getFloat(1);
                logger.info("avg:     " + avg);
                //logger.info("avg:     " + avg);
            }
        } catch (Exception exe) {
            exe.printStackTrace();
        }
        return null;
    }
    @GetMapping("/count/{schemaName}/{tableName}/{fieldName}")
    public Double getCountData(@PathVariable String schemaName,@PathVariable String tableName,@PathVariable String fieldName) {
        Connection conn;
        try {
            conn = JDBCUtils.getConnection("gigaspaces","localhost","4174",schemaName,"","");
            Statement st = conn.createStatement();
            String query = "SELECT COUNT("+fieldName+") " + "FROM "+tableName;
            logger.info("query: "+query);
            st = conn.createStatement();
            ResultSet rs = st.executeQuery(query);
            while (rs.next()) {
                float avg = rs.getFloat(1);
                logger.info("avg:     " + avg);
                //logger.info("avg:     " + avg);
            }
        } catch (Exception exe) {
            exe.printStackTrace();
        }
        return null;
    }
    @GetMapping("/data/{schemaName}/{tableName}/{fieldName}")
    public Double getData(@PathVariable String schemaName,@PathVariable String tableName,@PathVariable String fieldName) {
        Connection conn;
        try {
            conn = JDBCUtils.getConnection("gigaspaces","localhost","4174",schemaName,"","");
            Statement st = conn.createStatement();
            String query = "SELECT COUNT("+fieldName+") " + "FROM "+tableName;
            logger.info("query: "+query);
            st = conn.createStatement();
            ResultSet rs = st.executeQuery(query);
            while (rs.next()) {
                float avg = rs.getFloat(1);
                logger.info("avg:     " + avg);
                //logger.info("avg:     " + avg);
            }
        } catch (Exception exe) {
            exe.printStackTrace();
        }
        return null;
    }
    @GetMapping("/compare/{test}")
    public Map<String,String> compareMeasurement(@PathVariable String test
            , @RequestParam String dataSource1Type
            , @RequestParam String dataSource1HostIp
            , @RequestParam String dataSource1Port
            , @RequestParam String username1
            , @RequestParam String password1
            , @RequestParam String schemaName1
            , @RequestParam String tableName1
            , @RequestParam String fieldName1
            , @RequestParam String dataSource2Type
            , @RequestParam String dataSource2HostIp
            , @RequestParam String dataSource2Port
            , @RequestParam String username2
            , @RequestParam String password2
            , @RequestParam String schemaName2
            , @RequestParam String tableName2
            , @RequestParam String fieldName2
            , @RequestParam String whereCondition
            , @RequestParam(defaultValue="0") int executionTime) {
        Connection conn;
        Map<String,String> response = new HashMap<>();
        try {
            Properties dbProperties = new Properties();
            dbProperties.setProperty("testType","Compare");
            dbProperties.setProperty("test",test);
            dbProperties.setProperty("whereCondition",whereCondition);

            dbProperties.setProperty("dataSource1Type",dataSource1Type);
            dbProperties.setProperty("dataSource1HostIp",dataSource1HostIp);
            dbProperties.setProperty("dataSource1Port",dataSource1Port);
            dbProperties.setProperty("username1",username1);
            dbProperties.setProperty("password1",password1);
            dbProperties.setProperty("schemaName1",schemaName1);
            dbProperties.setProperty("tableName1",tableName1);
            dbProperties.setProperty("fieldName1",fieldName1);

            dbProperties.setProperty("dataSource2Type",dataSource2Type);
            dbProperties.setProperty("dataSource2HostIp",dataSource2HostIp);
            dbProperties.setProperty("dataSource2Port",dataSource2Port);
            dbProperties.setProperty("username2",username2);
            dbProperties.setProperty("password2",password2);
            dbProperties.setProperty("schemaName2",schemaName2);
            dbProperties.setProperty("tableName2",tableName2);
            dbProperties.setProperty("fieldName2",fieldName2);

            if(executionTime == 0){
                TestTask task = new TestTask(TestTask.getMaxId(), System.currentTimeMillis(),dbProperties, "pending");
                String result = task.executeTask();
                response.put("response", result);
            }else{
                Calendar calScheduledTime = Calendar.getInstance();
                calScheduledTime.add(Calendar.MINUTE, executionTime);
                TaskQueue.setTask(new TestTask(TestTask.getMaxId(), calScheduledTime.getTimeInMillis()
                        ,dbProperties, "pending"));

                logger.info("Task scheduled and will be executed at "+calScheduledTime.getTime());
                response.put("response", "scheduled");

            }





            // Validation of type (table)
            /*float val1=0,val2=0;
            conn = JDBCUtils.getConnection(dataSource1Type,dataSource1HostIp,dataSource1Port,schemaName1,username1,password1);
            Statement st = conn.createStatement();
            String query = "SELECT "+test+"("+fieldName1+") " + "FROM "+tableName1;
            logger.info("query1: "+query);
            st = conn.createStatement();
            ResultSet rs = st.executeQuery(query);
            while (rs.next()) {
                val1 = rs.getFloat(1);
                logger.info("val1:     " + val1);
                //logger.info("avg:     " + avg);
            }

            conn = JDBCUtils.getConnection(dataSource2Type,dataSource2HostIp,dataSource2Port,schemaName2,username2,password2);
            st = conn.createStatement();
            query = "SELECT "+test+"("+fieldName2+") " + "FROM "+tableName2;
            logger.info("query2: "+query);
            st = conn.createStatement();
            rs = st.executeQuery(query);
            while (rs.next()) {
                val2 = rs.getFloat(1);
                logger.info("val2:     " + val2);
                //logger.info("avg:     " + avg);
            }

            if(val1 == val2){
                System.out.printf("PASS");
                response.put("response", "PASS");
                return response;
            }else{
                logger.info("==> Test Result: FAIL, Test type: "+test+", DataSource1 Result: "+val1+", DataSource2 Result: "+val2);
                response.put("response", "FAIL");
                return response;
            }*/
        } catch (Exception exe) {
            exe.printStackTrace();
            response.put("response", exe.getMessage());
            return response;
        }
        return response;
    }
    @GetMapping("/measure/{test}")
    public Map<String,String> measurement(@PathVariable String test
            , @RequestParam String dataSourceType
            , @RequestParam String dataSourceHostIp
            , @RequestParam String dataSourcePort
            , @RequestParam String username
            , @RequestParam String password
            , @RequestParam String schemaName
            , @RequestParam String tableName
            , @RequestParam String fieldName
            , @RequestParam String whereCondition
           // , @RequestParam String limitRecords
            , @RequestParam(defaultValue="0") int executionTime
          ) {
        Connection conn;
        Map<String,String> response = new HashMap<>();
        try {

            Properties dbProperties = new Properties();
            dbProperties.setProperty("testType","Measure");
            dbProperties.setProperty("test",test);
            dbProperties.setProperty("dataSourceType",dataSourceType);
            dbProperties.setProperty("dataSourceHostIp",dataSourceHostIp);
            dbProperties.setProperty("dataSourcePort",dataSourcePort);
            dbProperties.setProperty("username",username);
            dbProperties.setProperty("password",password);
            dbProperties.setProperty("schemaName",schemaName);
            dbProperties.setProperty("tableName",tableName);
            dbProperties.setProperty("fieldName",fieldName);
            dbProperties.setProperty("whereCondition",whereCondition);
            //dbProperties.setProperty("limitRecords",limitRecords);

            if(executionTime == 0){
                TestTask task = new TestTask(TestTask.getMaxId(), System.currentTimeMillis(),dbProperties, "pending");
                String result = task.executeTask();
                response.put("response", result);
            }else{
                Calendar calScheduledTime = Calendar.getInstance();
                calScheduledTime.add(Calendar.MINUTE, executionTime);
                TaskQueue.setTask(new TestTask(TestTask.getMaxId(), calScheduledTime.getTimeInMillis()
                        ,dbProperties, "pending"));

                logger.info("Task scheduled and will be executed at "+calScheduledTime.getTime());
                response.put("response", "scheduled");
            }
            return response;

        } catch (Exception exe) {
            exe.printStackTrace();
            response.put("response", exe.getMessage());
            return response;
        }
        // return null;
    }
    @GetMapping("/scheduledtasks")
    public Map<String,String> getScheduledTasks(){
        Map<String,String> response = new HashMap<>();
        List<TestTask> allTasks = new ArrayList<>();
        allTasks.addAll(TaskQueue.getTasks());
        allTasks.addAll(CompleteTaskQueue.getTasks());
        Collections.sort(allTasks, (left, right) -> Math.toIntExact(left.getId() - right.getId()));

        Gson gson = new Gson();
        // convert your list to json
        String jsonTaskList = gson.toJson(allTasks);
        // print your generated json
        System.out.println("jsonTaskList: " + jsonTaskList);
        response.put("response", jsonTaskList);
        return response;
    }

    @GetMapping("/query/{tableName}/{columnName}")
    public Map<String,String> query(@PathVariable String tableName,@PathVariable String columnName
            , @RequestParam String dataSourceHostIp
            , @RequestParam String dataSourcePort
            , @RequestParam String username
            , @RequestParam String password
            , @RequestParam String schemaName
            , @RequestParam(defaultValue="0") int executionTime){

        Properties dbProperties = new Properties();
        dbProperties.setProperty("testType","Measure");
        dbProperties.setProperty("test","max");
        dbProperties.setProperty("dataSourceType","gigaspaces");
        dbProperties.setProperty("dataSourceHostIp",dataSourceHostIp);
        dbProperties.setProperty("dataSourcePort",dataSourcePort);
        dbProperties.setProperty("username",username);
        dbProperties.setProperty("password",password);
        dbProperties.setProperty("schemaName",schemaName);
        dbProperties.setProperty("tableName",tableName);
        dbProperties.setProperty("fieldName",columnName);
        dbProperties.setProperty("whereCondition","");
        //dbProperties.setProperty("limitRecords",limitRecords);

        Map<String,String> response = new HashMap<>();
        if(executionTime == 0){
            TestTask task = new TestTask(TestTask.getMaxId(), System.currentTimeMillis(),dbProperties, "pending");
            String result = task.executeTask();
            response.put("response", result);
        }else{
            Calendar calScheduledTime = Calendar.getInstance();
            calScheduledTime.add(Calendar.MINUTE, executionTime);
            TaskQueue.setTask(new TestTask(TestTask.getMaxId(), calScheduledTime.getTimeInMillis()
                    ,dbProperties, "pending"));

            logger.info("Task scheduled and will be executed at "+calScheduledTime.getTime());
            response.put("response", "scheduled");
        }
        return response;
    }

}
