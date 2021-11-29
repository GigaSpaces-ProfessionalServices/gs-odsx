package com.gigaspaces.odsx.noderebalancer.model;

import com.gigaspaces.odsx.noderebalancer.event.Event;
import com.gigaspaces.odsx.noderebalancer.event.FlowEventPublisher;
import com.gigaspaces.odsx.noderebalancer.policy.ServerConfiguration;

import java.util.LinkedList;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.function.BiFunction;
import java.util.logging.Logger;

public class Context {

    private String contextName;

    private FlowEventPublisher eventPublisher;

    private ConcurrentMap<String,Object> values;

    private ServerConfiguration setServerConfiguration;

    private Map<String, String> parameters;

    //Optimism ?
    boolean serverUp = false;

    Logger logger = Logger.getLogger(Context.class.getName());


    public Context(String contextName, FlowEventPublisher eventPublisher){
        this.contextName = contextName;
        this.eventPublisher = eventPublisher;
        values = new ConcurrentHashMap<String, Object>();
       // setServerConfiguration = new ServerConfiguration("", new LinkedList<String>());
    }

    public Context(String contextName,  FlowEventPublisher eventPublisher, ServerConfiguration serverConfiguration){
        this(contextName, eventPublisher);
        setServerConfiguration (serverConfiguration);
    }

    public String getContextName(){
        return contextName;
    }

    public Object  getValue(String name) {
        return values.get(name);
    }

    public void setValue(String name,  Object value) {
        values.put(name, value);
    }

    public Object compute(String key, BiFunction<String, Object, Object> remappingUnfction){
       return  values.compute(key, remappingUnfction);
    }

    public void publishInternalEvent(Event event) {
        logger.info("Dispatching internal event to the queue : " + event);
        eventPublisher.enqueue(event);
    }

     void setServerConfiguration(ServerConfiguration serverConfiguration) {
        this.setServerConfiguration = serverConfiguration;
    }

    public ServerConfiguration getSetServerConfiguration(){
        return setServerConfiguration;
    }

    public int getContainerCount(){
        return getSetServerConfiguration().getZoneContainerCount(getSetServerConfiguration().getZones().iterator().next());
    }
    public int getNodeCount(){
        return getSetServerConfiguration().getServerGroup().size();
    }

    public void setParameters(Map<String, String> parameters) {
        this.parameters = parameters;
    }
    public Long getLongParameter(String parameter, Long defaultValue){
        String value = parameters.get(parameter);
        Long result;

        if(value == null){
            logger.warning(" No value found for the parameter %s, the default value %s will be used.". format(parameter, defaultValue));
            result = defaultValue;
        } else {
            try{
                result = Long.valueOf(value);
            }catch(NumberFormatException nfe){
                logger.warning(" Number format exception while obtaining parameter %s value %s. Default will be used.". format(parameter, value));
                result = defaultValue;
            }
        }
        return result;
    }

    public boolean isServerUp() {
        return serverUp;
    }

    public  void setServerUp(boolean serverUp){
        this.serverUp = serverUp;
    }
}
