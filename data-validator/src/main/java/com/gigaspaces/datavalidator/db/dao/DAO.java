package com.gigaspaces.datavalidator.db.dao;

import java.util.List;

public interface DAO<T> {
	
	void add(T t);

	List<T> getAll();

	T getById(long id);

	void update(T t);

	void deleteById(int id);

	void deleteById(String className, int id);

	public long getAutoIncId(String dbTable, String tablePk);
}
