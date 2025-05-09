package com.readify.server.infrastructure.utils.file;

import java.io.InputStream;
import java.nio.file.Path;

public interface FileStorage {
    void store(String storageName, InputStream inputStream);
    InputStream retrieve(String storageName);
    void delete(String storageName);
    Path getStoragePath(String storageName);
} 