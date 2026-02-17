package com.graphrag.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@ComponentScan(basePackages = "com.graphrag")
public class GraphRagApplication {

    public static void main(String[] args) {
        SpringApplication.run(GraphRagApplication.class, args);
    }
}
