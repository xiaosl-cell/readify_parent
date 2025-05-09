package com.readify.server.infrastructure.utils.file;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;

@Component
@RequiredArgsConstructor
public class LocalFileStorage implements FileStorage {
    
    @Value("${readify.file.storage-path}")
    private String storagePath;

    @Override
    public void store(String storageName, InputStream inputStream) {
        try {
            Path targetPath = getStoragePath(storageName);
            Files.createDirectories(targetPath.getParent());
            Files.copy(inputStream, targetPath, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            throw new RuntimeException("Failed to store file", e);
        }
    }

    @Override
    public InputStream retrieve(String storageName) {
        try {
            Path filePath = getStoragePath(storageName);
            return Files.newInputStream(filePath);
        } catch (IOException e) {
            throw new RuntimeException("Failed to retrieve file", e);
        }
    }

    @Override
    public void delete(String storageName) {
        try {
            Path filePath = getStoragePath(storageName);
            Files.deleteIfExists(filePath);
        } catch (IOException e) {
            throw new RuntimeException("Failed to delete file", e);
        }
    }

    @Override
    public Path getStoragePath(String storageName) {
        return Paths.get(storagePath).resolve(storageName);
    }
} 