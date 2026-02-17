package com.graphrag.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@ComponentScan(basePackages = "com.graphrag")
@EnableScheduling
public class GraphRagApplication {

    public static void main(String[] args) {
        SpringApplication.run(GraphRagApplication.class, args);
    }
}
