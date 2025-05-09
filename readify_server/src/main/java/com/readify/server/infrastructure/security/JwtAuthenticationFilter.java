package com.readify.server.infrastructure.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    private final JwtTokenProvider jwtTokenProvider;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        try {
            String jwt = resolveToken(request);
            log.debug("Resolved token: {}", jwt);
            
            if (StringUtils.hasText(jwt)) {
                boolean isValid = jwtTokenProvider.validateToken(jwt);
                log.debug("Token validation result: {}", isValid);
                
                if (isValid) {
                    Authentication authentication = jwtTokenProvider.getAuthentication(jwt);
                    log.debug("Authentication object created: {}", authentication);
                    SecurityContextHolder.getContext().setAuthentication(authentication);
                    log.debug("Authentication object set in SecurityContext");

                    // 存储用户信息到ThreadLocal
                    UserInfo userInfo = new UserInfo(
                            (Long) authentication.getCredentials(),
                            authentication.getName()
                    );
                    SecurityUtils.setCurrentUser(userInfo);
                    log.debug("User info stored in ThreadLocal: {}", userInfo);
                }
            }
        } catch (Exception e) {
            log.error("认证过程发生错误", e);
            SecurityUtils.clearCurrentUser();
        }

        try {
            filterChain.doFilter(request, response);
        } finally {
            // 请求结束后清理ThreadLocal
            SecurityUtils.clearCurrentUser();
        }
    }

    private String resolveToken(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        log.debug("Authorization header: {}", bearerToken);
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
} 