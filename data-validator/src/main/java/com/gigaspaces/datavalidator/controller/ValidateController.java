package com.gigaspaces.datavalidator.controller;

import com.gigaspaces.datavalidator.TaskProcessor.CompleteTaskQueue;
import com.gigaspaces.datavalidator.TaskProcessor.TaskQueue;
import com.gigaspaces.datavalidator.db.service.DataSourceService;
import com.gigaspaces.datavalidator.db.service.MeasurementService;
import com.gigaspaces.datavalidator.db.service.TestTaskService;
import com.gigaspaces.datavalidator.model.DataSource;
import com.gigaspaces.datavalidator.model.DataSourceRequestModel;
import com.gigaspaces.datavalidator.model.Measurement;
import com.gigaspaces.datavalidator.model.MeasurementRequestModel;
import com.gigaspaces.datavalidator.model.ModelConstant;
import com.gigaspaces.datavalidator.model.TestTask;
import com.google.gson.Gson;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;

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
    @Autowired
    private DataSourceService dataSourceService;
    
    private Logger logger = Logger.getLogger(this.getClass().getName());

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
    @PostMapping(path = "/measurement/register", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    public Map<String,String> registerMeasurement(@RequestBody MeasurementRequestModel measurementRequestModel) {
        Map<String,String> response = new HashMap<>();
        try {
            Measurement measurement = new Measurement(measurementService.getAutoIncId()
                    , Long.parseLong(measurementRequestModel.getDataSourceId())
                    ,measurementRequestModel.getTest()
                    , measurementRequestModel.getSchemaName(), measurementRequestModel.getTableName()
                    , measurementRequestModel.getFieldName()
                    , "-1",measurementRequestModel.getWhereCondition());
            measurement.setStatus(ModelConstant.ACTIVE);
            measurementService.add(measurement);
            response.put("response", "Measurement Registered successfully");
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

            Measurement measurement = measurementService.getMeasurement(Long.parseLong(measurementId));
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
                logger.info("Task scheduled and will be executed at "+calScheduledTime.getTime());
                response.put("response", "scheduled");
            }
            TaskQueue.setTask(task);
            odsxTaskService.add(task);

        } catch (Exception exe) {
            exe.printStackTrace();
            response.put("response", exe.getMessage());
        }

        return response;
    }
    @DeleteMapping("/measurement/remove/{measurementId}")
    public Map<String,String> removeMeasurement(@PathVariable String measurementId
            , @RequestParam(defaultValue="0") int executionTime
    ) {
        Map<String,String> response = new HashMap<>();
        try {
        	 Measurement measurement = measurementService.getMeasurement(Long.parseLong(measurementId));
        	 measurement.setStatus(ModelConstant.DELETED);
            measurementService.update(measurement);
            response.put("response", "Measurement with id '"+measurementId+"' is removed");
            return response;

        } catch (Exception exe) {
            exe.printStackTrace();
            response.put("response", exe.getMessage());
            return response;
        }
    }
    @PostMapping(path = "/measurement/update", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    public Map<String,String> updateMeasurement(@RequestBody MeasurementRequestModel measurementRequestModel) {
        Map<String,String> response = new HashMap<>();
        try {
            Measurement measurement = measurementService.getMeasurement(Long.parseLong(measurementRequestModel.getMeasurementId()));
            measurement.setType(measurementRequestModel.getTest());
//            measurement.setDataSourceType(measurementRequestModel.getDataSourceType());
//            measurement.setDataSourceHostIp(measurementRequestModel.getDataSourceHostIp());
//            measurement.setDataSourcePort(measurementRequestModel.getDataSourcePort());
//            measurement.setUsername(measurementRequestModel.getUsername());
//            measurement.setPassword(measurementRequestModel.getPassword());
            measurement.setSchemaName(measurementRequestModel.getSchemaName());
            measurement.setTableName(measurementRequestModel.getTableName());
            measurement.setFieldName(measurementRequestModel.getFieldName());
            measurement.setWhereCondition(measurementRequestModel.getWhereCondition());
            measurement.setLimitRecords("-1");
            //measurement.setIntegratedSecurity(measurementRequestModel.getIntegratedSecurity());
            measurementService.update(measurement);
            response.put("response", "Measurement with id '"+measurementRequestModel.getMeasurementId()+"' updated successfully");
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
        List<Measurement> measurementList = measurementService.getActiveMeasurement();
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
            , @RequestParam(defaultValue="0") int executionTime
            , @PathVariable String integratedSecurity){

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

    
    @PostMapping(path = "/datasource/register", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    public Map<String,String> registerDtasource(@RequestBody DataSourceRequestModel dataSourceRequestModel) {
        Map<String,String> response = new HashMap<>();
        try {
        	DataSource dataSource=new DataSource(
        			 dataSourceService.getAutoIncId()
        			,dataSourceRequestModel.getDataSourceName()
        			,dataSourceRequestModel.getDataSourceType()
        			,dataSourceRequestModel.getDataSourceHostIp()
        			,dataSourceRequestModel.getDataSourcePort()
        			,dataSourceRequestModel.getUsername()
        			,dataSourceRequestModel.getPassword()
        			);
        	dataSource.setAuthenticationScheme(dataSourceRequestModel.getAuthenticationScheme());
        	dataSource.setIntegratedSecurity(dataSourceRequestModel.getIntegratedSecurity());
        	dataSource.setProperties(dataSourceRequestModel.getProperties());
        	dataSource.setStatus(ModelConstant.ACTIVE);
        	dataSourceService.add(dataSource);
            response.put("response", "DataSource added successfully");
            return response;

        } catch (Exception exe) {
            exe.printStackTrace();
            response.put("response", exe.getMessage());
            return response;
        }
    }

    @GetMapping("/datasource/list")
    public Map<String,String> getDtasourceList(){
        Map<String,String> response = new HashMap<>();
        List<DataSource> dataSourceList = dataSourceService.getActiveDataSources();
        logger.info("datasourceList size: "+dataSourceList.size());
        Gson gson = new Gson();
        String jsonTaskList = gson.toJson(dataSourceList);
        response.put("response", jsonTaskList);
        return response;
    }
    
    @PostMapping(path = "/datasource/update", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
	public Map<String, String> updateDtasource(@RequestBody DataSourceRequestModel dataSourceRequestModel) {
		Map<String, String> response = new HashMap<>();
		try {
			DataSource dataSource = dataSourceService.getDataSource(Long.parseLong(dataSourceRequestModel.getDataSourceId()));
			dataSource.setDataSourceName(dataSourceRequestModel.getDataSourceName());
			dataSource.setDataSourceType(dataSourceRequestModel.getDataSourceType());
			dataSource.setDataSourceHostIp(dataSourceRequestModel.getDataSourceHostIp());
			dataSource.setDataSourcePort(dataSourceRequestModel.getDataSourcePort());
			dataSource.setUsername(dataSourceRequestModel.getUsername());
			dataSource.setPassword(dataSourceRequestModel.getPassword());
			dataSource.setAuthenticationScheme(dataSourceRequestModel.getAuthenticationScheme());
        	dataSource.setIntegratedSecurity(dataSourceRequestModel.getIntegratedSecurity());
        	dataSource.setProperties(dataSourceRequestModel.getProperties());
			dataSourceService.update(dataSource);
			response.put("response","Datasource with id '" + dataSourceRequestModel.getDataSourceId() + "' updated successfully");
		} catch (Exception exe) {
			exe.printStackTrace();
			response.put("response", exe.getMessage());
			return response;
		}
		return response;
	}
    
    @DeleteMapping("/datasource/remove/{datasourceId}")
    public Map<String,String> removeDataSource(@PathVariable String datasourceId
            , @RequestParam(defaultValue="0") int executionTime
    ) {
        Map<String,String> response = new HashMap<>();
        try {
        	DataSource dataSource = dataSourceService.getDataSource(Long.parseLong(datasourceId));
        	dataSource.setStatus(ModelConstant.DELETED);
        	dataSourceService.update(dataSource);
            response.put("response", "DataSource with id '"+datasourceId+"' is removed");
            return response;
        } catch (Exception exe) {
            exe.printStackTrace();
            response.put("response", exe.getMessage());
            return response;
        }
    }
    
}
