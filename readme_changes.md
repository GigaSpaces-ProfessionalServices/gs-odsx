1 app.config
   app.xap.workLocation=/dbagigadata
2. app.yaml
   gs:
    jars:
      spaceupdatecachepolicy:
         jar: tierdirectcall.jar
3. Create directory /dbagigashare/current/gs/jars/spaceupdatecachepolicy/
4. Build tierdirectcall.jar from CSM repo and copy to above location.