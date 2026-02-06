package com.readify.server.config;

import com.readify.server.domain.auth.service.RbacService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class RbacBootstrap implements CommandLineRunner {
    private final RbacService rbacService;

    @Override
    public void run(String... args) {
        try {
            rbacService.ensureDefaultRoleForExistingUsers();
            log.info("RBAC default role bootstrap completed");
        } catch (Exception e) {
            log.warn("RBAC bootstrap skipped: {}", e.getMessage());
        }
    }
}
