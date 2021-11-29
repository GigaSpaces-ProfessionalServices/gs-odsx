package com.gigaspaces.odsx.noderebalancer.util;

import com.gigaspaces.odsx.noderebalancer.ClusterConfigurationReader;
import com.gigaspaces.odsx.noderebalancer.action.BaseAction;
import com.gigaspaces.odsx.noderebalancer.action.Status;
import com.gigaspaces.odsx.noderebalancer.model.Context;

import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * There is need to highlight certain occurrences during flow lifecycle e.g
 * - Change of workflow state
 * - Exiting stable state
 * - Returning back to stable state
 * This helps scanning through logs. This class provides such highlighted logging.
 *
 */
public class BannerPrinter  {

    private static final int LINE_CHAR_COUNT = 80;
    private int lineCount;
    private char lineChar;
    Level logLevel;

    static Logger logger = Logger.getLogger(BannerPrinter.class.getName());


    /**
     *
     * @param lineCount - number of lines to use to highlight the message
     * @param lineChar  - character to use for line
     * @param logLevel - Logging level to use
     */
    public BannerPrinter(  int lineCount, char lineChar, Level logLevel) {
        this.lineCount = lineCount;
        this.lineChar = lineChar;
        this.logLevel = logLevel;
    }

    /**
     * Create with default values
     */
    public BannerPrinter( ) {
        this(  1, '*', Level.INFO);
    }

    /**
     * Print the message to appear as a banner
     */
    public void print(String message)  {
        if(lineCount <  0){
            lineCount = 1;
        }

        String line = getLine(lineChar, LINE_CHAR_COUNT);
        printLine(line);
        logger.log(logLevel, message);
        printLine(line);

    }

    private void printLine(String line) {
        for (int i = 0; i < lineCount; i++){
            logger.log(logLevel, line);
        }
    }

    private String getLine(char lineChar, int count) {
        StringBuffer line = new StringBuffer("");
        for (int i = 0; i < count; i++){
            line.append(lineChar);
        }
        return line.toString();
    }
}
