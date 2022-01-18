echo "USAGE: $0 [-daemon] [-name servicename] classname [opts]"
base_dir=$(pwd)
# Which java to use
if [ -z "$JAVA_HOME" ]; then
  JAVA="java"
else
  JAVA="$JAVA_HOME/bin/java"
fi
# Log directory to use
if [ "x$LOG_DIR" = "x" ]; then
  LOG_DIR="$base_dir/logs"
fi
# Memory options
if [ -z "$ADABAS_HEAP_OPTS" ]; then
  ADABAS_HEAP_OPTS="-Xmx256M"
fi
if [ -z "$ADABAS_JVM_PERFORMANCE_OPTS" ]; then
  ADABAS_JVM_PERFORMANCE_OPTS="\
-server -XX:+UseG1GC -XX:MaxGCPauseMillis=20 -XX:InitiatingHeapOccupancyPercent=35 \
-XX:+ExplicitGCInvokesConcurrent -XX:MaxInlineLevel=15 -Djava.awt.headless=true"
fi
if [ -z "$ADABAS_SLF4J_OPTS" ]; then
  # Log to console. This is a tool.
  SLF4J_DIR="$base_dir/config/slf4j.properties"
  ADABAS_SLF4J_OPTS="-Dslf4j.configuration=file:${SLF4J_DIR}"
fi
  # create logs directory
if [ ! -d "$LOG_DIR" ]; then
  mkdir -p "$LOG_DIR"
fi
# Generic jvm settings you want to add
if [ -z "$CLASSPATH" ]; then
  CLASSPATH="adabas-0.0.1-SNAPSHOT.jar"
fi

# Generic jvm settings you want to add
if [ -z "$ADABAS_OPTS" ]; then
  ADABAS_OPTS="\
-Dorg.slf4j.simpleLogger.defaultLogLevel=DEBUG \
-Dcom.ibm.jsse2.overrideDefaultTLS=true \
-Dcom.ibm.mq.cfg.useIBMCipherMappings=false \
-Dspring.config.location=file:config/application.yml \
-Djavax.net.ssl.keyStore=keystore.jks -Djavax.net.ssl.keyStorePassword=123456 -Djavax.net.ssl.trustStore=keystore.jks \
-Djavax.net.ssl.trustStorePassword=123456 -Djavax.net.debug=ssl,keymanager"
fi
while [ $# -gt 0 ]; do
  COMMAND=$1
  case $COMMAND in
    -name)
      DAEMON_NAME=$2
      CONSOLE_OUTPUT_FILE=$LOG_DIR/$DAEMON_NAME.out
      shift 2
      ;;
    -daemon)
      DAEMON_MODE="true"
      shift
      ;;
    *)
      break
      ;;
  esac
done
if [ -z "$CONSOLE_OUTPUT_FILE" ]; then
  CONSOLE_OUTPUT_FILE="$LOG_DIR/adabas_publisher.out"
fi
if [ "x$DAEMON_MODE" = "xtrue" ]; then
 nohup "$JAVA" $ADABAS_HEAP_OPTS $ADABAS_JVM_PERFORMANCE_OPTS $ADABAS_SLF4J_OPTS -cp "$CLASSPATH" $ADABAS_OPTS -jar "$@" > "$CONSOLE_OUTPUT_FILE" 2>&1 < /dev/null &
else
exec "$JAVA" $ADABAS_HEAP_OPTS $ADABAS_JVM_PERFORMANCE_OPTS $ADABAS_SLF4J_OPTS $ADABAS_OPTS -jar "$CLASSPATH" "$@"
fi

