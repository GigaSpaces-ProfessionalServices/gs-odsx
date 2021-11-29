package com.bofleumi.gsadmin;

import org.openspaces.admin.Admin;
import org.openspaces.admin.AdminFactory;

import java.nio.file.Files;
import java.nio.file.Paths;


public class MyAdmin {
    protected String locator;
    // lookup group can be null, we don't actually need it to connect to Gigaspaces
    protected String lookupGroup;
    protected Admin admin;
    protected String username;
    protected String password;

    public MyAdmin() {
    }

    protected void initAdmin() {
        AdminFactory af = new AdminFactory();
        af.addLocator(locator);

        if (lookupGroup != null && !"".equals(lookupGroup)) {
            af.addGroup(lookupGroup);
        }

        if (username != null && password != null) {
            af.credentials(username, password);
        }
        admin = af.createAdmin();
    }

    protected void readPasswordFile(String filename) throws java.io.IOException {
        try {
            password = new String(Files.readAllBytes(Paths.get(filename))).trim();
        } catch (java.io.IOException ex) {
            ex.printStackTrace();
            throw (ex);
        }
    }

}

