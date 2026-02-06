package com.readify.server.infrastructure.security;

import com.readify.server.domain.auth.model.ApiKey;
import com.readify.server.domain.auth.service.RbacService;
import com.readify.server.domain.auth.service.ApiKeyService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.HashSet;
import java.util.Set;
import java.util.stream.Collectors;

@Slf4j
@Component
@RequiredArgsConstructor
public class ApiKeyAuthenticationFilter extends OncePerRequestFilter {
    private final ApiKeyService apiKeyService;
    private final RbacService rbacService;
    private static final String API_KEY_HEADER = "X-API-Key";

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        try {
            String apiKey = resolveApiKey(request);
            log.debug("Resolved API Key: {}", apiKey);
            
            if (StringUtils.hasText(apiKey)) {
                ApiKey key = apiKeyService.validate(apiKey);
                log.debug("API Key validation result: {}", key != null);
                
                if (key != null) {
                    Set<SimpleGrantedAuthority> authorities = new HashSet<>();
                    authorities.add(new SimpleGrantedAuthority("ROLE_API_USER"));
                    authorities.addAll(
                            rbacService.getRoleAuthorities(key.getUserId())
                                    .stream()
                                    .map(SimpleGrantedAuthority::new)
                                    .collect(Collectors.toSet())
                    );
                    authorities.addAll(
                            rbacService.getPermissionAuthorities(key.getUserId())
                                    .stream()
                                    .map(SimpleGrantedAuthority::new)
                                    .collect(Collectors.toSet())
                    );
                    UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                            "API_USER_" + key.getUserId(),
                            key.getUserId(),
                            authorities
                    );
                    SecurityContextHolder.getContext().setAuthentication(authentication);
                    log.debug("API Key authentication successful for user ID: {}", key.getUserId());

                    // 存储用户信息到ThreadLocal
                    UserInfo userInfo = new UserInfo(key.getUserId(), "API_USER_" + key.getUserId());
                    SecurityUtils.setCurrentUser(userInfo);
                    log.debug("User info stored in ThreadLocal: {}", userInfo);
                }
            }
        } catch (Exception e) {
            log.error("API Key认证过程发生错误", e);
            SecurityUtils.clearCurrentUser();
        }

        try {
            filterChain.doFilter(request, response);
        } finally {
            SecurityUtils.clearCurrentUser();
        }
    }

    private String resolveApiKey(HttpServletRequest request) {
        return request.getHeader(API_KEY_HEADER);
    }
} 
