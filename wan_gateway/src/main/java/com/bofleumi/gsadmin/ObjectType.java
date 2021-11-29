package com.bofleumi.gsadmin;

import com.gigaspaces.annotation.pojo.SpaceId;

public class ObjectType {
    private String className;
    private Boolean allowWrite;
    private Boolean allowUpdate;
    private Boolean allowTake;

    public ObjectType() {
    }
    public ObjectType(String className) {
        this.className = className;
        this.allowWrite=true;

    }

    @SpaceId
    public String getClassName() {
        return className;
    }

    public void setClassName(String className) {
        this.className = className;
    }

    public Boolean getAllowWrite() {
        return allowWrite;
    }

    public void setAllowWrite(Boolean allowWrite) {
        this.allowWrite = allowWrite;
    }

    public Boolean getAllowUpdate() {
        return allowUpdate;
    }

    public void setAllowUpdate(Boolean allowUpdate) {
        this.allowUpdate = allowUpdate;
    }

    public Boolean getAllowTake() {
        return allowTake;
    }

    public void setAllowTake(Boolean allowTake) {
        this.allowTake = allowTake;
    }

    @Override
    public String toString() {
        return "ObjectType{" +
                "className='" + className + '\'' +
                ", allowWrite=" + allowWrite +
                ", allowUpdate=" + allowUpdate +
                ", allowTake=" + allowTake +
                '}';
    }
    public String toCsv(){
        return className+","+allowWrite+","+allowUpdate+","+allowTake;
    }
    public ObjectType fromCsv(String line){
        String[] values = line.split(",");
        ObjectType ot = new ObjectType();
        if(values.length >=4) {
            ot.setClassName(values[0]);
            ot.setAllowWrite(Boolean.parseBoolean(values[1]));
            ot.setAllowUpdate(Boolean.parseBoolean(values[2]));
            ot.setAllowTake(Boolean.parseBoolean(values[3]));
        }
        return ot;

    }
}
