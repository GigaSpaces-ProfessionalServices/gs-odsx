package com.gigaspaces.datavalidator.controller;

import com.gigaspaces.datavalidator.TaskProcessor.CompleteTaskQueue;
import com.gigaspaces.datavalidator.TaskProcessor.TaskQueue;
import com.gigaspaces.datavalidator.db.service.MeasurementService;
import com.gigaspaces.datavalidator.db.service.TestTaskService;
import com.gigaspaces.datavalidator.model.Measurement;
import com.gigaspaces.datavalidator.model.TestTask;
import com.google.gson.Gson;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import java.sql.Connection;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;

@RestController
public class ValidateController {
	
	@Autowired
	private TestTaskService odsxTaskService;
	@Autowired
	private MeasurementService measurementService;

	private Logger logger = Logger.getLogger(this.getClass().getName());

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

            TestTask task;
            List<Measurement> measurementList = new LinkedList<Measurement>();
            measurementList.add(measurement1);
            measurementList.add(measurement2);

            if(executionTime == 0){
                task = new TestTask(odsxTaskService.getAutoIncId(), System.currentTimeMillis()
                        ,"Compare", measurementList);
                String result = task.executeTask();
                response.put("response", result);
            }else{
                Calendar calScheduledTime = Calendar.getInstance();
                calScheduledTime.add(Calendar.MINUTE, executionTime);
				task = new TestTask(odsxTaskService.getAutoIncId(), calScheduledTime.getTimeInMillis()
                        ,"Compare", measurementList);
                TaskQueue.setTask(task);
                logger.info("Task scheduled and will be executed at "+calScheduledTime.getTime());
                response.put("response", "scheduled");
            }
            
            odsxTaskService.add(task);
            
        } catch (Exception exe) {
            exe.printStackTrace();
            response.put("response", exe.getMessage());
        }

        return response;
    
    }
    
    @GetMapping("/compare/{measurementId1}/{measurementId2}")
    public Map<String,String> compareMeasurement(@PathVariable String measurementId1
            ,@PathVariable String measurementId2
            ,@RequestParam(defaultValue="0") int executionTime) {
        
    	Map<String,String> response = new HashMap<>();
        
        try {
        	
			Measurement measurement1 = measurementService.getMeasurement(Integer.parseInt(measurementId1));
			Measurement measurement2 = measurementService.getMeasurement(Integer.parseInt(measurementId2));

            TestTask task;
            List<Measurement> measurementList = new LinkedList<>();
            measurementList.add(measurement1);
            measurementList.add(measurement2);
            
            if(executionTime == 0){
                
            	task = new TestTask(odsxTaskService.getAutoIncId(), System.currentTimeMillis()
                        ,"Compare", measurementList);
                String result = task.executeTask();
                response.put("response", result);
                
            }else{
                
            	Calendar calScheduledTime = Calendar.getInstance();
                calScheduledTime.add(Calendar.MINUTE, executionTime);
                task =new TestTask(odsxTaskService.getAutoIncId(), calScheduledTime.getTimeInMillis()
                        ,"Compare", measurementList);
                TaskQueue.setTask(task);
                logger.info("Task scheduled and will be executed at "+calScheduledTime.getTime());
                response.put("response", "scheduled");
            
            }

            odsxTaskService.add(task);
            
        } catch (Exception exe) {
            exe.printStackTrace();
            response.put("response", exe.getMessage());
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
        
    	Map<String,String> response = new HashMap<>();
        
    	try {
        	
            Measurement measurement = new Measurement(measurementService.getAutoIncId(), test, dataSourceType, dataSourceHostIp, dataSourcePort
                    , username, password, schemaName
                    , tableName, fieldName, "-1",whereCondition);
            
            measurementService.add(measurement);

            List<Measurement> measurementList = new LinkedList<>();
            measurementList.add(measurement);
            TestTask task;
            
            if(executionTime == 0){
                task = new TestTask(odsxTaskService.getAutoIncId(), System.currentTimeMillis()
                        ,"Measure",measurementList);
                String result = task.executeTask();
                response.put("response", result);
            }else{
                Calendar calScheduledTime = Calendar.getInstance();
                calScheduledTime.add(Calendar.MINUTE, executionTime);
                task = new TestTask(odsxTaskService.getAutoIncId(), calScheduledTime.getTimeInMillis()
                        ,"Measure", measurementList);
                TaskQueue.setTask(task);
                logger.info("Task scheduled and will be executed at "+calScheduledTime.getTime());
                response.put("response", "scheduled");
            }
            
            odsxTaskService.add(task);

        } catch (Exception exe) {
            exe.printStackTrace();
            response.put("response", exe.getMessage());
        }
        
        return response;
    }

    @GetMapping("/measurement/register")
    public Map<String,String> registerMeasurement(@RequestParam String test
            , @RequestParam String dataSourceType
            , @RequestParam String dataSourceHostIp
            , @RequestParam String dataSourcePort
            , @RequestParam String username
            , @RequestParam String password
            , @RequestParam String schemaName
            , @RequestParam String tableName
            , @RequestParam String fieldName
            , @RequestParam String whereCondition
            //, @RequestParam String limitRecords
    ) {
        
    	Map<String,String> response = new HashMap<>();
        
    	try {
            Measurement measurement = new Measurement(measurementService.getAutoIncId(), test, dataSourceType, dataSourceHostIp, dataSourcePort
                    , username, password, schemaName
                    , tableName, fieldName, "-1",whereCondition);
            measurementService.add(measurement);
            response.put("response", "Registered successfully");
            return response;

        } catch (Exception exe) {
            exe.printStackTrace();
            response.put("response", exe.getMessage());
            return response;
        }
    }
    
    @GetMapping("/measurement/run/{measurementId}")
    public Map<String,String> runMeasurement(@PathVariable String measurementId
            , @RequestParam(defaultValue="0") int executionTime
    ) {
    	
        Map<String,String> response = new HashMap<>();
        
        try {
        	
            Measurement measurement = measurementService.getMeasurement(Integer.parseInt(measurementId));
            List<Measurement> measurementList = new LinkedList<Measurement>();
            measurementList.add(measurement);
            TestTask task;
            
            if(executionTime == 0){
                
            	task = new TestTask(odsxTaskService.getAutoIncId(), System.currentTimeMillis()
                        ,"Measure",measurementList);
                String result = task.executeTask();
                response.put("response", result);
            
            }else{
            
            	Calendar calScheduledTime = Calendar.getInstance();
                calScheduledTime.add(Calendar.MINUTE, executionTime);
                task = new TestTask(odsxTaskService.getAutoIncId(), calScheduledTime.getTimeInMillis()
                        ,"Measure", measurementList);
                TaskQueue.setTask(task);
                logger.info("Task scheduled and will be executed at "+calScheduledTime.getTime());
                response.put("response", "scheduled");
            }
            
            odsxTaskService.add(task);

        } catch (Exception exe) {
            exe.printStackTrace();
            response.put("response", exe.getMessage());
        }
        
        return response;
    }
    
    @GetMapping("/scheduledtasks")
    public Map<String,String> getScheduledTasks(){
         
    	 Map<String,String> response = new HashMap<>();
        List<TestTask> allTasks = new ArrayList<TestTask>();
        allTasks.addAll(TaskQueue.getTasks());        
        allTasks.addAll(CompleteTaskQueue.getTasks());
        Collections.sort(allTasks, (left, right) -> Math.toIntExact(left.getId() - right.getId()));
        Gson gson = new Gson();
        String jsonTaskList = gson.toJson(allTasks);
        response.put("response", jsonTaskList);
        
        return response;
    }
    
    @GetMapping("/measurement/list")
    public Map<String,String> getMeasurementList(){
        
    	Map<String,String> response = new HashMap<>();
        List<Measurement> measurementList = measurementService.getAll();
        logger.info("measurementList size: "+measurementList.size());
        Collections.sort(measurementList, (left, right) -> Math.toIntExact(left.getId() - right.getId()));
        Gson gson = new Gson();
        String jsonTaskList = gson.toJson(measurementList);
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
     
        measurementService.add(measurement);
        
        List<Measurement> measurementList = new LinkedList<Measurement>();
        measurementList.add(measurement);
       
        TestTask task;
        Map<String,String> response = new HashMap<>();

        if(executionTime == 0){
 
        	task = new TestTask(odsxTaskService.getAutoIncId(), System.currentTimeMillis()
                    ,testType, measurementList);
            String result = task.executeTask();
            response.put("response", result);
       
        }else{
        
        	Calendar calScheduledTime = Calendar.getInstance();
            calScheduledTime.add(Calendar.MINUTE, executionTime);
            task=new TestTask(odsxTaskService.getAutoIncId(), calScheduledTime.getTimeInMillis()
                    ,testType, measurementList);
            TaskQueue.setTask(task);
            logger.info("Task scheduled and will be executed at "+calScheduledTime.getTime());
            response.put("response", "scheduled");
        
        }
        odsxTaskService.add(task);
        
        return response;
    }

}
