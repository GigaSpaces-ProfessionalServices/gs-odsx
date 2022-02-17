package com.gigaspaces.datavalidator.db;

import org.hibernate.HibernateException;
import org.hibernate.SessionFactory;
import org.hibernate.cfg.Configuration;
import org.hibernate.cfg.Environment;
import org.hibernate.service.ServiceRegistry;
import org.hibernate.service.ServiceRegistryBuilder;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import java.util.Properties;

@Component
public class HibernateUtil {

	private SessionFactory sessionFactory = null;
	private ServiceRegistry serviceRegistry = null;

	@Autowired
	private DbProperties dbProperties;

	public SessionFactory configureSessionFactory() throws HibernateException {
		if (sessionFactory == null) {
			Properties properties = new Properties();
			properties.put(Environment.SHOW_SQL, dbProperties.isShow_sql());
			properties.put(Environment.FORMAT_SQL, dbProperties.isFormat_sql());
			properties.put(Environment.DIALECT, dbProperties.getDialect());
			properties.put(Environment.DRIVER, dbProperties.getDriver());
			properties.put(Environment.URL, dbProperties.getConnection_url());
			properties.put(Environment.USER, dbProperties.getUser());
			properties.put(Environment.PASS, dbProperties.getPass());
			if (dbProperties.getHbm2dll_auto() != null) {
				properties.put(Environment.HBM2DDL_AUTO, dbProperties.getHbm2dll_auto());
			}
			Configuration configuration = new Configuration();
			configuration.setProperties(properties);
			configuration.addResource("Measurement.hbm.xml");
			configuration.addResource("TestTask.hbm.xml");
			configuration.addResource("DataSource.hbm.xml");
			serviceRegistry = new ServiceRegistryBuilder().applySettings(properties).buildServiceRegistry();
			sessionFactory = configuration.buildSessionFactory(serviceRegistry);
		}

		return sessionFactory;
	}

}
