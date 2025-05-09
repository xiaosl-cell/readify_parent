package com.readify.server;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@MapperScan("com.readify.server.infrastructure.persistence.mapper")
public class ReadifyServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(ReadifyServerApplication.class, args);
    }

}
