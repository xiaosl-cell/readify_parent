package com.readify.server.domain.file.service.impl;

import com.readify.server.domain.file.model.File;
import com.readify.server.domain.file.repository.FileRepository;
import com.readify.server.domain.file.service.FileService;
import com.readify.server.infrastructure.common.exception.NotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.InputStream;
import java.util.List;

@Service
@RequiredArgsConstructor
public class FileServiceImpl implements FileService {
    private final FileRepository fileRepository;

    @Override
    public File upload(String originalFilename, String mimeType, long size, InputStream inputStream) {
        return fileRepository.upload(originalFilename, mimeType, size, inputStream);
    }

    @Override
    public void delete(Long fileId) {
        fileRepository.deleteById(fileId);
    }

    @Override
    public File getFileInfo(Long fileId) {
        return fileRepository.findById(fileId)
                .orElseThrow(() -> new NotFoundException("文件不存在！"));
    }

    @Override
    public List<File> getFilesByIds(List<Long> fileIds) {
        return fileRepository.findAllById(fileIds);
    }


    @Override
    public File updateVectorizedStatus(Long fileId, Boolean vectorized) {
        File file = fileRepository.updateVectorizedStatus(fileId, vectorized);
        if (file == null) {
            throw new NotFoundException("文件不存在！");
        }
        return file;
    }

    @Override
    public List<File> getNonVectorizedFiles() {
        return fileRepository.findNonVectorizedFiles();
    }
} 