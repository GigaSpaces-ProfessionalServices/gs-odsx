package com.gigaspaces.datavalidator.controller;

import com.gigaspaces.datavalidator.utils.JDBCUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.sql.*;
import java.util.HashMap;
import java.util.Map;
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
    @GetMapping("/count/{schemaName}/{tableName}/{fieldName}")
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
            , @RequestParam String fieldName2) {
        Connection conn;
        Map<String,String> response = new HashMap<>();
        try {
            // Validation of type (table)
            float val1=0,val2=0;
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
                response.put("message", "PASS");
                return response;
            }else{
                logger.info("==> Test Result: FAIL, Test type: "+test+", DataSource1 Result: "+val1+", DataSource2 Result: "+val2);
                response.put("message", "FAIL");
                return response;
            }
        } catch (Exception exe) {
            exe.printStackTrace();
            response.put("message", exe.getMessage());
            return response;
        }
       // return null;
    }
}
