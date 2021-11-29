package com.gigaspaces.healthcheckservice.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.yaml.snakeyaml.Yaml;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.List;
import java.util.Map;


@RestController
public class HealthCheckController {
    @Value("${app.services.filepath}")
    private String servicesFilePath;

    @GetMapping("/health")
    public String healthcheck() {
        String[] serviceNames = new String[]{"kapacitor", "influxd", "grafana"};
        if (servicesFilePath != null && !"".equals(servicesFilePath)) {
            System.out.println(servicesFilePath);
            Yaml yaml = new Yaml();
            try (InputStream inputStream = new FileInputStream(servicesFilePath)) {
                Map<String, Object> obj = yaml.load(inputStream);
                List<String> services = (List<String>) obj.get("serviceName");
                System.out.println(services);
                serviceNames = services.toArray(new String[0]);
            } catch (Exception e) {
                System.out.println("exception occured while reading file");
                System.out.println(e.getMessage());
            }

        }
        String response = "healthy";
        for (String serviceName : serviceNames) {
            String serverStatus[] = new String[]{"systemctl", "is-active", serviceName};
            try {
                final Process process = new ProcessBuilder(serverStatus).redirectErrorStream(true).start();
                process.waitFor();
                InputStream in = process.getInputStream();
                BufferedReader br = new BufferedReader(new InputStreamReader(in));
                if ("inactive".equals(br.readLine())) {
                    response = "fail";
                    break;
                }
                System.out.println(serviceName + " status : " + br.readLine());
            } catch (Exception e) {
                e.printStackTrace();
                response = "fail";
            }
        }
        return response;
    }
}
