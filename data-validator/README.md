# ODSX - Data Validation Service
The following was discovered as part of building this project:

### Build and Run Application
* Maven Build from data-validator directory 
  > mvn clean install -DskipTests
* Run command 
  > java -jar target/data-validator-0.0.1-SNAPSHOT.jar

### Register Measurement

* Start ODSX cli and follow the below option
  > Menu -> Data Validator -> Perform Validation -> Select 'Measure' -> enter 'yes' for register
*  Enter the host where data validation service app is running
* Enter the details for Measurement (following example)
  > Test type (count/avg/min/max/sum) [count]: avg 
   
  > DataSource Type (gigaspaces/ms-sql/db2/mysql) [gigaspaces]: gigaspaces
  
  > DataSource Host Ip [localhost]: localhost
  
  > DataSource Port [4174]:
  
  >  User name []:
  
  >  Password []:
  
  >  Schema Name [demo]:
  
  >  Table Name : com.mycompany.app.Person
  
  >  Field Name : salary
  
  >  Where Condition [''] : 
  
### Run/Schedule Measurement Test

* Start ODSX cli and follow the below option
  > Menu -> Data Validator -> Perform Validation -> Select 'Measure' -> enter 'no' for register -> Select measurement by id to run

*  Enter the host where data validation service app is running
*  Enter execution time delay. Pass '0' to execute it now otherwise number represents minutes delay to schedule it for future execution

### Run/Schedule Compare Test

* Start ODSX cli and follow the below option
  > Menu -> Data Validator -> Perform Validation -> Select 'Compare'

*  Enter the host where data validation service app is running
*  Select measurement by id to be compared in the test   
*  Enter execution time delay. Pass '0' to execute it now otherwise number represents minutes delay to schedule it for future execution


### List Scheduled Tests

* Start ODSX cli and follow the below option
  > Menu -> Data Validator -> Perform Validation -> Select 'List of scheduled tests'

*  Enter the host where data validation service app is running