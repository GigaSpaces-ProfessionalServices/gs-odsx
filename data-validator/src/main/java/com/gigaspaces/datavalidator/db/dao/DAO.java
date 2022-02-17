package com.gigaspaces.datavalidator.db.dao;

import java.util.List;

public interface DAO<T> {
	
	void add(T t);

	List<T> getAll();

	List<T> getAll(String sql);
	T getById(long id);

	void update(T t);

	void deleteById(long id);

	void deleteById(String className, long id);

	public long getAutoIncId(String dbTable, String tablePk);
}
