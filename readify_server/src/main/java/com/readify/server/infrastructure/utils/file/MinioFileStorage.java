package com.readify.server.infrastructure.utils.file;

import io.minio.BucketExistsArgs;
import io.minio.GetObjectArgs;
import io.minio.MakeBucketArgs;
import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import io.minio.RemoveObjectArgs;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.InputStream;

@Component
public class MinioFileStorage implements FileStorage {

    private static final long PART_SIZE = 10L * 1024L * 1024L;

    @Value("${readify.file.minio.endpoint}")
    private String endpoint;

    @Value("${readify.file.minio.access-key}")
    private String accessKey;

    @Value("${readify.file.minio.secret-key}")
    private String secretKey;

    @Value("${readify.file.minio.bucket}")
    private String defaultBucket;

    private MinioClient client;

    @PostConstruct
    void init() {
        client = MinioClient.builder()
                .endpoint(endpoint)
                .credentials(accessKey, secretKey)
                .build();
        ensureBucket(defaultBucket);
    }

    @Override
    public void store(String bucket, String storageKey, InputStream inputStream) {
        try {
            client.putObject(
                    PutObjectArgs.builder()
                            .bucket(bucket)
                            .object(storageKey)
                            .stream(inputStream, -1, PART_SIZE)
                            .build()
            );
        } catch (Exception e) {
            throw new RuntimeException("Failed to store file", e);
        }
    }

    @Override
    public InputStream retrieve(String bucket, String storageKey) {
        try {
            return client.getObject(
                    GetObjectArgs.builder()
                            .bucket(bucket)
                            .object(storageKey)
                            .build()
            );
        } catch (Exception e) {
            throw new RuntimeException("Failed to retrieve file", e);
        }
    }

    @Override
    public void delete(String bucket, String storageKey) {
        try {
            client.removeObject(
                    RemoveObjectArgs.builder()
                            .bucket(bucket)
                            .object(storageKey)
                            .build()
            );
        } catch (Exception e) {
            throw new RuntimeException("Failed to delete file", e);
        }
    }

    @Override
    public String getStorageLocation(String bucket, String storageKey) {
        return "s3://" + bucket + "/" + storageKey;
    }

    private void ensureBucket(String bucket) {
        try {
            boolean exists = client.bucketExists(
                    BucketExistsArgs.builder()
                            .bucket(bucket)
                            .build()
            );
            if (!exists) {
                client.makeBucket(
                        MakeBucketArgs.builder()
                                .bucket(bucket)
                                .build()
                );
            }
        } catch (Exception e) {
            throw new RuntimeException("Failed to ensure bucket: " + bucket, e);
        }
    }
}
