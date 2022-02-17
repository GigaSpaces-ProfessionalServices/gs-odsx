package com.gigaspaces.datavalidator.db.impl;

import org.hibernate.Query;
import org.hibernate.SQLQuery;
import org.hibernate.Session;
import org.hibernate.Transaction;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.GenericTypeResolver;
import org.springframework.stereotype.Component;

import com.gigaspaces.datavalidator.db.HibernateUtil;
import com.gigaspaces.datavalidator.db.dao.DAO;
import java.util.List;

@Component
public abstract class DAOImplAbstract<T> implements DAO<T> {

	protected final Class<T> genericType;
	private final String RECORD_COUNT_HQL;
	private final String FIND_ALL_HQL;
	
	@Autowired
	private HibernateUtil hibernateUtil;

	@SuppressWarnings("unchecked")
	public DAOImplAbstract() {
		this.genericType = (Class<T>) GenericTypeResolver.resolveTypeArgument(getClass(), DAOImplAbstract.class);
		this.RECORD_COUNT_HQL = "select count(*) from " + this.genericType.getName();
		this.FIND_ALL_HQL = "from " + this.genericType.getName() + " t ";
	}

	@Override
	public void add(T t) {
		Transaction trns = null;
		Session session = hibernateUtil.configureSessionFactory().openSession();
		try {
			trns = session.beginTransaction();
			session.save(t);
			session.getTransaction().commit();
		} catch (RuntimeException e) {
			if (trns != null) {
				trns.rollback();
			}
			e.printStackTrace();
		} finally {
			session.flush();
			session.close();
		}
	}

	@Override
	public List<T> getAll() {
		List<T> users = null;
		Session session = hibernateUtil.configureSessionFactory().openSession();
		try {
			String query = "from " + this.genericType.getName();
			users = session.createQuery(query).list();
		} catch (RuntimeException e) {
			e.printStackTrace();
		} finally {
			session.flush();
			session.close();
		}
		return users;
	}
	
	@Override
	public List<T> getAll(String query) {
		List<T> users = null;
		Session session = hibernateUtil.configureSessionFactory().openSession();
		try {
			users = session.createQuery(query).list();
		} catch (RuntimeException e) {
			e.printStackTrace();
		} finally {
			session.flush();
			session.close();
		}
		return users;
	}

	@Override
	public T getById(long id) {
		T contact = null;
		Session session = hibernateUtil.configureSessionFactory().openSession();
		try {
			String queryString = " from " + this.genericType.getName() + " where id = :id";
			Query query = session.createQuery(queryString);
			query.setLong("id", id);
			contact = (T) query.uniqueResult();
		} catch (RuntimeException e) {
			e.printStackTrace();
		} finally {
			session.flush();
			session.close();
		}
		return contact;
	}

	@Override
	public void update(T t) {
		Transaction trns = null;
		Session session = hibernateUtil.configureSessionFactory().openSession();
		try {
			trns = session.beginTransaction();
			session.update(t);
			session.getTransaction().commit();
		} catch (RuntimeException e) {
			if (trns != null) {
				trns.rollback();
			}
			e.printStackTrace();
		} finally {
			session.flush();
			session.close();
		}
	}

	@Override
	public void deleteById(long id) {
		String classname = getClass().getName();
		deleteById(classname, id);
	}

	@Override
	public void deleteById(String className, long id) {

		Transaction trns = null;
		Session session = hibernateUtil.configureSessionFactory().openSession();
		try {
			trns = session.beginTransaction();
			T contact = (T) session.load(this.genericType.getName(), new Long(id));
			session.delete(contact);
			session.getTransaction().commit();
		} catch (RuntimeException e) {
			if (trns != null) {
				trns.rollback();
			}
			e.printStackTrace();
		} finally {
			session.flush();
			session.close();
		}
	}

	@Override
	public long getAutoIncId(String dbTable, String tablePk) {
		long id = 0;
		Session session = hibernateUtil.configureSessionFactory().openSession();
		try {
			String sql = "select max(tt." + tablePk + ") from " + dbTable + " tt";
			SQLQuery query = session.createSQLQuery(sql);
			id = (Integer) query.uniqueResult();
		} catch (RuntimeException e) {
			e.printStackTrace();
		} finally {
			session.flush();
			session.close();
		}
		return ++id;
	}

}
