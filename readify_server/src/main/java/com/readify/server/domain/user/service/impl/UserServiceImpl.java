package com.readify.server.domain.user.service.impl;

import com.readify.server.domain.user.model.User;
import com.readify.server.domain.user.repository.UserRepository;
import com.readify.server.domain.user.service.UserService;
import com.readify.server.infrastructure.common.exception.BusinessException;
import com.readify.server.infrastructure.common.exception.NotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {
    private final UserRepository userRepository;

    @Override
    public User createUser(User user) {
        if (userRepository.existsByUsername(user.getUsername())) {
            throw new BusinessException("用户名已存在");
        }
        user.setEnabled(true);
        user.setCreateTime(System.currentTimeMillis());
        user.setUpdateTime(System.currentTimeMillis());
        return userRepository.save(user);
    }

    @Override
    public User updateUser(User user) {
        User existingUser = getUserById(user.getId());
        user.setCreateTime(existingUser.getCreateTime());
        user.setEnabled(existingUser.getEnabled());
        user.setUpdateTime(System.currentTimeMillis());
        return userRepository.save(user);
    }

    @Override
    public void deleteUser(Long id) {
        if (userRepository.findById(id).isEmpty()) {
            throw new NotFoundException("用户不存在");
        }
        userRepository.deleteById(id);
    }

    @Override
    public User getUserById(Long id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("用户不存在"));
    }

    @Override
    public User getUserByUsername(String username) {
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new NotFoundException("用户不存在"));
    }

    @Override
    public List<User> getAllUsers() {
        return userRepository.findAll();
    }

    @Override
    public boolean isUsernameExists(String username) {
        return userRepository.existsByUsername(username);
    }
} 