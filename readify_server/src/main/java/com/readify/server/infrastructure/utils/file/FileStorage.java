package com.readify.server.infrastructure.utils.file;

import java.io.InputStream;

public interface FileStorage {
    void store(String bucket, String storageKey, InputStream inputStream);
    InputStream retrieve(String bucket, String storageKey);
    void delete(String bucket, String storageKey);
    String getStorageLocation(String bucket, String storageKey);
}
