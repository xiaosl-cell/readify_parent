package com.readify.server.domain.auth.service.impl;

import com.readify.server.domain.auth.model.AuthUser;
import com.readify.server.domain.auth.model.LoginResult;
import com.readify.server.domain.auth.repository.AuthUserRepository;
import com.readify.server.domain.auth.service.AuthService;
import com.readify.server.domain.auth.service.RbacService;
import com.readify.server.infrastructure.common.exception.BusinessException;
import com.readify.server.infrastructure.common.exception.UnauthorizedException;
import com.readify.server.infrastructure.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {
    private final AuthUserRepository authUserRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final RbacService rbacService;

    @Override
    @Transactional
    public AuthUser register(String username, String password) {
        log.info("Start register user: {}", username);

        if (authUserRepository.existsByUsername(username)) {
            throw new BusinessException("用户名已存在");
        }

        AuthUser authUser = new AuthUser();
        authUser.setUsername(username);
        authUser.setPassword(passwordEncoder.encode(password));
        authUser.setEnabled(true);
        authUser.setCreateTime(System.currentTimeMillis());
        authUser.setUpdateTime(System.currentTimeMillis());

        AuthUser savedUser = authUserRepository.save(authUser);
        grantDefaultRole(savedUser.getId());
        log.info("User register success: {}", username);
        return savedUser;
    }

    @Override
    public LoginResult login(String username, String password) {
        log.info("User login: {}", username);

        AuthUser authUser = authUserRepository.findByUsername(username);
        if (authUser == null) {
            throw new UnauthorizedException("用户名或密码错误");
        }

        if (!passwordEncoder.matches(password, authUser.getPassword())) {
            throw new UnauthorizedException("用户名或密码错误");
        }

        if (!authUser.getEnabled()) {
            throw new UnauthorizedException("账户已被禁用");
        }

        String token = jwtTokenProvider.generateToken(authUser);
        log.info("User login success: {}", username);

        return new LoginResult(authUser, token);
    }

    @Override
    public void grantDefaultRole(Long userId) {
        rbacService.grantDefaultRoleForUser(userId);
    }
}

