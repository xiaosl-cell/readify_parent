package com.readify.server.infrastructure.utils.file;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;

@Deprecated
@RequiredArgsConstructor
public class LocalFileStorage implements FileStorage {
    // Deprecated: local file storage is no longer supported. Keep class only for reference.
    @Value("${readify.file.storage-path}")
    private String storagePath;

    @Override
    public void store(String bucket, String storageKey, InputStream inputStream) {
        try {
            Path targetPath = getStoragePath(storageKey);
            Files.createDirectories(targetPath.getParent());
            Files.copy(inputStream, targetPath, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            throw new RuntimeException("Failed to store file", e);
        }
    }

    @Override
    public InputStream retrieve(String bucket, String storageKey) {
        try {
            Path filePath = getStoragePath(storageKey);
            return Files.newInputStream(filePath);
        } catch (IOException e) {
            throw new RuntimeException("Failed to retrieve file", e);
        }
    }

    @Override
    public void delete(String bucket, String storageKey) {
        try {
            Path filePath = getStoragePath(storageKey);
            Files.deleteIfExists(filePath);
        } catch (IOException e) {
            throw new RuntimeException("Failed to delete file", e);
        }
    }

    @Override
    public String getStorageLocation(String bucket, String storageKey) {
        return getStoragePath(storageKey).toString();
    }

    private Path getStoragePath(String storageKey) {
        return Paths.get(storagePath).resolve(storageKey);
    }
}
