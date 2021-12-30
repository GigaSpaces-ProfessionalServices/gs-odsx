package com.gigaspaces.datavalidator.controller;

import com.fasterxml.jackson.databind.annotation.JsonAppend;
import com.gigaspaces.datavalidator.TaskProcessor.CompleteTaskQueue;
import com.gigaspaces.datavalidator.TaskProcessor.TaskQueue;
import com.gigaspaces.datavalidator.TaskProcessor.TestTask;
import com.gigaspaces.datavalidator.model.Measurement;
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
            Measurement measurement1 = new Measurement(Measurement.getMaxId(), test, dataSource1Type
                    , dataSource1HostIp, dataSource1Port
                    , username1, password1, schemaName1
                    , tableName1, fieldName1,"-1", whereCondition);

            Measurement measurement2 = new Measurement(Measurement.getMaxId(), test
                    , dataSource2Type, dataSource2HostIp, dataSource2Port
                    , username2, password2, schemaName2
                    , tableName2, fieldName2,"-1", whereCondition);

            List<Measurement> measurementList = new LinkedList<>();
            measurementList.add(measurement1);
            measurementList.add(measurement2);

            if(executionTime == 0){
                TestTask task = new TestTask(TestTask.getMaxId(), System.currentTimeMillis()
                        ,"Compare", measurementList);
                String result = task.executeTask();
                response.put("response", result);
            }else{
                Calendar calScheduledTime = Calendar.getInstance();
                calScheduledTime.add(Calendar.MINUTE, executionTime);
                TaskQueue.setTask(new TestTask(TestTask.getMaxId(), calScheduledTime.getTimeInMillis()
                        ,"Compare", measurementList));

                logger.info("Task scheduled and will be executed at "+calScheduledTime.getTime());
                response.put("response", "scheduled");
            }
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
            Measurement measurement = new Measurement(Measurement.getMaxId(), test, dataSourceType, dataSourceHostIp, dataSourcePort
                    , username, password, schemaName
                    , tableName, fieldName, "-1",whereCondition);

            List<Measurement> measurementList = new LinkedList<>();
            measurementList.add(measurement);
            if(executionTime == 0){
                TestTask task = new TestTask(TestTask.getMaxId(), System.currentTimeMillis()
                        ,"Measure",measurementList);
                String result = task.executeTask();
                response.put("response", result);
            }else{
                Calendar calScheduledTime = Calendar.getInstance();
                calScheduledTime.add(Calendar.MINUTE, executionTime);
                TaskQueue.setTask(new TestTask(TestTask.getMaxId(), calScheduledTime.getTimeInMillis()
                        ,"Measure", measurementList));

                logger.info("Task scheduled and will be executed at "+calScheduledTime.getTime());
                response.put("response", "scheduled");
            }
            return response;

        } catch (Exception exe) {
            exe.printStackTrace();
            response.put("response", exe.getMessage());
            return response;
        }
    }
    @GetMapping("/scheduledtasks")
    public Map<String,String> getScheduledTasks(){
        Map<String,String> response = new HashMap<>();
        List<TestTask> allTasks = new ArrayList<>();
        allTasks.addAll(TaskQueue.getTasks());
        allTasks.addAll(CompleteTaskQueue.getTasks());
        Collections.sort(allTasks, (left, right) -> Math.toIntExact(left.getId() - right.getId()));

        Gson gson = new Gson();
        String jsonTaskList = gson.toJson(allTasks);
        logger.info("jsonTaskList: " + jsonTaskList);
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

        String dataSourceType="gigaspaces";
        String test="max";
        String testType = "Measure";
        Measurement measurement = new Measurement(Measurement.getMaxId(), test
                , dataSourceType, dataSourceHostIp, dataSourcePort
                , username, password, schemaName
                , tableName, columnName,"-1", "");

        List<Measurement> measurementList = new LinkedList<>();
        measurementList.add(measurement);


        Map<String,String> response = new HashMap<>();
        if(executionTime == 0){
            TestTask task = new TestTask(TestTask.getMaxId(), System.currentTimeMillis()
                    ,testType, measurementList);
            String result = task.executeTask();
            response.put("response", result);
        }else{
            Calendar calScheduledTime = Calendar.getInstance();
            calScheduledTime.add(Calendar.MINUTE, executionTime);
            TaskQueue.setTask(new TestTask(TestTask.getMaxId(), calScheduledTime.getTimeInMillis()
                    ,testType, measurementList));

            logger.info("Task scheduled and will be executed at "+calScheduledTime.getTime());
            response.put("response", "scheduled");
        }
        return response;
    }

}
