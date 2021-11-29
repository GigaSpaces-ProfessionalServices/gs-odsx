package com.gigaspaces.odsx.noderebalancer.admin.model;

public class AdminConfiguration {
    protected String[] locators ={""};
    protected String lookupGroup;
    protected String userName;
    protected String password;

    public AdminConfiguration(String userName, String password,  String[] locators, String lookupGroup) {
        this.userName = userName;
        this.password = password;
        this.locators = locators;
        this.lookupGroup = lookupGroup;
    }

    public String[] getLocators() {
        return locators;
    }

    public String getLookupGroup() {
        return lookupGroup;
    }

    public String getUserName() {
        return userName;
    }

    public String getPassword() {
        return password;
    }
}
