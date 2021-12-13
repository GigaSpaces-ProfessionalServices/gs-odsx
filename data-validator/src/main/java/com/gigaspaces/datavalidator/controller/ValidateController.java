package com.gigaspaces.datavalidator.controller;

import org.openspaces.core.GigaSpace;
import org.openspaces.core.GigaSpaceConfigurer;
import org.openspaces.core.space.SpaceProxyConfigurer;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ValidateController {

    @GetMapping("/hello")
    public String hello() {

        return "hello";
    }

    @GetMapping("/avg")
    public Double getAverageData() {

        return null;
    }

    @GetMapping("/count")
    public int getCountData() {
        GigaSpace gigaSpace = new GigaSpaceConfigurer(new SpaceProxyConfigurer("demo").lookupLocators("172.31.34.174").lookupGroups("xap-16.0.0")).gigaSpace();

        return gigaSpace.count(new Object());
    }
}
