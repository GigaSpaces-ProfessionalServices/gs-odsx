package integration;//import org.slf4j.Logger;
//import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.logging.*;

/**
 * This class uses Java assertion.
 * Must be run with -ea argument to the Java command line (or VM argument if launching from IDE)
 */

public class LogTest {

    public static void main (String args[]) throws IOException {
        assert System.getProperty("java.util.logging.config.file") != null : "Missing Logging Config file VM property";
        Logger logger = Logger.getLogger(LogTest.class.getName());
        logger.info("Hello World\n");
        LogManager.getLogManager().readConfiguration();
        String propertyValue = LogManager.getLogManager().getProperty("com.gigaspaces.logger.RollingFileHandler.filename-pattern");
        assert propertyValue != null : "Missing log file name";

    }
}
