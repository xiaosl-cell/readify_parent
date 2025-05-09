package com.readify.server.domain.auth.service.impl;

import com.readify.server.domain.auth.model.AuthUser;
import com.readify.server.domain.auth.model.LoginResult;
import com.readify.server.domain.auth.repository.AuthUserRepository;
import com.readify.server.domain.auth.service.AuthService;
import com.readify.server.infrastructure.security.JwtTokenProvider;
import com.readify.server.infrastructure.common.exception.BusinessException;
import com.readify.server.infrastructure.common.exception.UnauthorizedException;
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

    @Override
    @Transactional
    public AuthUser register(String username, String password) {
        log.info("开始注册用户: {}", username);
        
        // 检查用户名是否已存在
        if (authUserRepository.existsByUsername(username)) {
            throw new BusinessException("用户名已存在");
        }

        // 创建新用户
        AuthUser authUser = new AuthUser();
        authUser.setUsername(username);
        authUser.setPassword(passwordEncoder.encode(password));
        authUser.setEnabled(true);
        authUser.setCreateTime(System.currentTimeMillis());
        authUser.setUpdateTime(System.currentTimeMillis());

        // 保存用户
        AuthUser savedUser = authUserRepository.save(authUser);
        log.info("用户注册成功: {}", username);
        return savedUser;
    }

    @Override
    public LoginResult login(String username, String password) {
        log.info("用户登录: {}", username);
        
        // 获取用户信息
        AuthUser authUser = authUserRepository.findByUsername(username);
        if (authUser == null) {
            throw new UnauthorizedException("用户名或密码错误");
        }
        
        // 验证密码
        if (!passwordEncoder.matches(password, authUser.getPassword())) {
            throw new UnauthorizedException("用户名或密码错误");
        }

        // 检查账户状态
        if (!authUser.getEnabled()) {
            throw new UnauthorizedException("账户已被禁用");
        }

        // 生成token
        String token = jwtTokenProvider.generateToken(authUser);
        log.info("用户登录成功: {}", username);
        
        return new LoginResult(authUser, token);
    }
} 