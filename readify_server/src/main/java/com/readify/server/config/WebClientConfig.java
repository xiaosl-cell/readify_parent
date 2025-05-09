package com.readify.server.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {
    
    @Value("${readify.vector-service.url:http://localhost:8090}")
    private String vectorServiceUrl;
    
    @Value("${readify.agent-service.url:http://localhost:8090}")
    private String agentServiceUrl;
    
    @Bean
    public WebClient vectorServiceClient() {
        return WebClient.builder()
                .baseUrl(vectorServiceUrl)
                .build();
    }
    
    @Bean
    public WebClient webClient() {
        return WebClient.builder()
                .baseUrl(agentServiceUrl)
                .build();
    }
} 