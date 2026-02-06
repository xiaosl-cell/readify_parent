package com.readify.server.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.readify.server.domain.file.model.File;
import com.readify.server.domain.file.repository.FileRepository;
import com.readify.server.infrastructure.persistence.converter.FileConverter;
import com.readify.server.infrastructure.persistence.entity.FileEntity;
import com.readify.server.infrastructure.persistence.entity.ProjectFileEntity;
import com.readify.server.infrastructure.persistence.mapper.FileMapper;
import com.readify.server.infrastructure.persistence.mapper.ProjectFileMapper;
import com.readify.server.infrastructure.utils.file.FileStorage;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Repository;
import org.springframework.util.DigestUtils;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@Repository
@RequiredArgsConstructor
public class FileRepositoryImpl implements FileRepository {

    private final FileMapper fileMapper;
    private final ProjectFileMapper projectFileMapper;
    private final FileStorage fileStorage;
    private final FileConverter fileConverter = FileConverter.INSTANCE;

    @Value("${readify.file.minio.bucket}")
    private String storageBucket;

    @Value("${readify.file.storage-type:minio}")
    private String storageType;

    @Override
    public File save(File file) {
        FileEntity entity = fileConverter.toEntity(file);
        if (entity.getId() == null) {
            fileMapper.insert(entity);
        } else {
            fileMapper.updateById(entity);
        }
        return fileConverter.toDomain(entity);
    }

    @Override
    public Optional<File> findById(Long id) {
        Optional<File> fileOptional = Optional.ofNullable(fileMapper.selectById(id))
                .map(fileConverter::toDomain);
        if (fileOptional.isEmpty()) {
            return Optional.empty();
        }
        File file = fileOptional.get();
        List<ProjectFileEntity> projectFileEntities = projectFileMapper.selectList(
                new LambdaQueryWrapper<ProjectFileEntity>()
                        .eq(ProjectFileEntity::getFileId, id)
                        .last("LIMIT 1"));
        if (projectFileEntities.isEmpty()) {
            return Optional.of(file);
        }
        ProjectFileEntity projectFile = projectFileEntities.get(0);
        file.setProjectId(projectFile.getProjectId());
        file.setUserId(projectFile.getUserId());
        return Optional.of(file);
    }

    @Override
    public List<File> findAllById(List<Long> ids) {
        return fileMapper.selectBatchIds(ids).stream()
                .map(fileConverter::toDomain)
                .collect(Collectors.toList());
    }

    @Override
    public Optional<File> findByMd5(String md5) {
        FileEntity entity = fileMapper.selectOne(
                new LambdaQueryWrapper<FileEntity>()
                        .eq(FileEntity::getMd5, md5)
                        .last("LIMIT 1"));
        return Optional.ofNullable(entity)
                .map(fileConverter::toDomain);
    }

    @Override
    public void deleteById(Long id) {
        FileEntity fileEntity = fileMapper.selectById(id);
        deletePhysicalFile(fileEntity.getStorageBucket(), fileEntity.getStorageKey());
        fileMapper.deleteById(id);
    }

    @Override
    public File upload(String originalFilename, String mimeType, long size, InputStream inputStream) {
        try {
            // Read all bytes to compute MD5 and allow multiple use of the stream.
            byte[] bytes = inputStream.readAllBytes();

            String md5 = DigestUtils.md5DigestAsHex(bytes);

            return findByMd5(md5).orElseGet(() -> {
                String storageKey = generateStorageKey(originalFilename);
                try (InputStream newInputStream = new ByteArrayInputStream(bytes)) {
                    fileStorage.store(storageBucket, storageKey, newInputStream);

                    File file = File.builder()
                            .originalName(originalFilename)
                            .storageKey(storageKey)
                            .storageBucket(storageBucket)
                            .storageType(storageType)
                            .size(size)
                            .mimeType(mimeType)
                            .md5(md5)
                            .createTime(System.currentTimeMillis())
                            .updateTime(System.currentTimeMillis())
                            .deleted(false)
                            .vectorized(false)
                            .build();

                    return save(file);
                } catch (IOException e) {
                    throw new RuntimeException("Failed to store file", e);
                }
            });
        } catch (IOException e) {
            throw new RuntimeException("Failed to upload file", e);
        }
    }

    @Override
    public void deletePhysicalFile(String storageBucket, String storageKey) {
        fileStorage.delete(storageBucket, storageKey);
    }

    private String generateStorageKey(String originalFilename) {
        String extension = "";
        int lastDotIndex = originalFilename.lastIndexOf('.');
        if (lastDotIndex > 0) {
            extension = originalFilename.substring(lastDotIndex);
        }
        return UUID.randomUUID().toString() + extension;
    }

    @Override
    public File updateVectorizedStatus(Long fileId, Boolean vectorized) {
        FileEntity entity = fileMapper.selectById(fileId);
        if (entity != null) {
            entity.setVectorized(vectorized);
            entity.setUpdateTime(System.currentTimeMillis());
            fileMapper.updateById(entity);
            return fileConverter.toDomain(entity);
        }
        return null;
    }

    @Override
    public List<File> findNonVectorizedFiles() {
        List<FileEntity> entities = fileMapper.selectList(
                new LambdaQueryWrapper<FileEntity>()
                        .eq(FileEntity::getVectorized, false));
        return entities.stream()
                .map(fileConverter::toDomain)
                .collect(Collectors.toList());
    }
}
