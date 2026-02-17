package com.graphrag.common.storage.service;

import com.graphrag.common.storage.config.MinioProperties;
import io.minio.*;
import io.minio.http.Method;
import io.minio.messages.DeleteError;
import io.minio.messages.DeleteObject;
import io.minio.messages.Item;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

/**
 * MinIO 文件存储服务类
 * 提供文件上传、下载、删除、检查等核心功能
 *
 * @author GraphRAG Team
 */
@Slf4j
@Service
@RequiredArgsConstructor
@ConditionalOnBean(MinioClient.class)
public class MinioService {

    private final MinioClient minioClient;
    private final MinioProperties minioProperties;

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMdd");

    /**
     * 初始化默认存储桶
     * 如果配置了自动创建存储桶，则在服务启动时检查并创建存储桶
     */
    public void initDefaultBucket() {
        if (Boolean.TRUE.equals(minioProperties.getAutoCreateBucket())) {
            try {
                String bucketName = minioProperties.getBucketName();
                if (!bucketExists(bucketName)) {
                    createBucket(bucketName);
                    log.info("自动创建存储桶成功: {}", bucketName);
                }
            } catch (Exception e) {
                log.error("初始化默认存储桶失败", e);
            }
        }
    }

    /**
     * 检查存储桶是否存在
     *
     * @param bucketName 存储桶名称
     * @return 是否存在
     */
    public boolean bucketExists(String bucketName) {
        try {
            return minioClient.bucketExists(BucketExistsArgs.builder()
                    .bucket(bucketName)
                    .build());
        } catch (Exception e) {
            log.error("检查存储桶是否存在失败: {}", bucketName, e);
            return false;
        }
    }

    /**
     * 创建存储桶
     *
     * @param bucketName 存储桶名称
     * @return 是否创建成功
     */
    public boolean createBucket(String bucketName) {
        try {
            minioClient.makeBucket(MakeBucketArgs.builder()
                    .bucket(bucketName)
                    .build());
            log.info("创建存储桶成功: {}", bucketName);
            return true;
        } catch (Exception e) {
            log.error("创建存储桶失败: {}", bucketName, e);
            return false;
        }
    }

    /**
     * 删除存储桶
     *
     * @param bucketName 存储桶名称
     * @return 是否删除成功
     */
    public boolean deleteBucket(String bucketName) {
        try {
            minioClient.removeBucket(RemoveBucketArgs.builder()
                    .bucket(bucketName)
                    .build());
            log.info("删除存储桶成功: {}", bucketName);
            return true;
        } catch (Exception e) {
            log.error("删除存储桶失败: {}", bucketName, e);
            return false;
        }
    }

    /**
     * 上传文件
     *
     * @param file 上传的文件
     * @return 文件访问路径
     * @throws Exception 上传异常
     */
    public String uploadFile(MultipartFile file) throws Exception {
        return uploadFile(file, null, null);
    }

    /**
     * 上传文件到指定存储桶
     *
     * @param file       上传的文件
     * @param bucketName 存储桶名称（为空则使用默认存储桶）
     * @return 文件访问路径
     * @throws Exception 上传异常
     */
    public String uploadFile(MultipartFile file, String bucketName) throws Exception {
        return uploadFile(file, bucketName, null);
    }

    /**
     * 上传文件到指定存储桶和路径
     *
     * @param file       上传的文件
     * @param bucketName 存储桶名称（为空则使用默认存储桶）
     * @param objectName 对象名称/路径（为空则自动生成）
     * @return 文件访问路径
     * @throws Exception 上传异常
     */
    public String uploadFile(MultipartFile file, String bucketName, String objectName) throws Exception {
        // 使用默认存储桶
        if (bucketName == null || bucketName.isEmpty()) {
            bucketName = minioProperties.getBucketName();
        }

        // 自动生成对象名称
        if (objectName == null || objectName.isEmpty()) {
            objectName = generateObjectName(file.getOriginalFilename());
        }

        // 检查存储桶是否存在，不存在则创建
        if (!bucketExists(bucketName)) {
            createBucket(bucketName);
        }

        // 上传文件
        minioClient.putObject(PutObjectArgs.builder()
                .bucket(bucketName)
                .object(objectName)
                .stream(file.getInputStream(), file.getSize(), -1)
                .contentType(file.getContentType())
                .build());

        log.info("文件上传成功: bucket={}, object={}", bucketName, objectName);

        // 返回文件访问路径
        return getFileUrl(bucketName, objectName);
    }

    /**
     * 通过输入流上传文件
     *
     * @param inputStream 输入流
     * @param bucketName  存储桶名称
     * @param objectName  对象名称
     * @param contentType 内容类型
     * @param size        文件大小
     * @return 文件访问路径
     * @throws Exception 上传异常
     */
    public String uploadFile(InputStream inputStream, String bucketName, String objectName,
                             String contentType, long size) throws Exception {
        // 使用默认存储桶
        if (bucketName == null || bucketName.isEmpty()) {
            bucketName = minioProperties.getBucketName();
        }

        // 检查存储桶是否存在
        if (!bucketExists(bucketName)) {
            createBucket(bucketName);
        }

        // 上传文件
        minioClient.putObject(PutObjectArgs.builder()
                .bucket(bucketName)
                .object(objectName)
                .stream(inputStream, size, -1)
                .contentType(contentType)
                .build());

        log.info("文件上传成功: bucket={}, object={}", bucketName, objectName);

        return getFileUrl(bucketName, objectName);
    }

    /**
     * 下载文件
     *
     * @param objectName 对象名称
     * @return 文件输入流
     * @throws Exception 下载异常
     */
    public InputStream downloadFile(String objectName) throws Exception {
        return downloadFile(null, objectName);
    }

    /**
     * 下载文件
     *
     * @param bucketName 存储桶名称（为空则使用默认存储桶）
     * @param objectName 对象名称
     * @return 文件输入流
     * @throws Exception 下载异常
     */
    public InputStream downloadFile(String bucketName, String objectName) throws Exception {
        if (bucketName == null || bucketName.isEmpty()) {
            bucketName = minioProperties.getBucketName();
        }

        return minioClient.getObject(GetObjectArgs.builder()
                .bucket(bucketName)
                .object(objectName)
                .build());
    }

    /**
     * 删除文件
     *
     * @param objectName 对象名称
     * @return 是否删除成功
     */
    public boolean deleteFile(String objectName) {
        return deleteFile(null, objectName);
    }

    /**
     * 删除文件
     *
     * @param bucketName 存储桶名称（为空则使用默认存储桶）
     * @param objectName 对象名称
     * @return 是否删除成功
     */
    public boolean deleteFile(String bucketName, String objectName) {
        if (bucketName == null || bucketName.isEmpty()) {
            bucketName = minioProperties.getBucketName();
        }

        try {
            minioClient.removeObject(RemoveObjectArgs.builder()
                    .bucket(bucketName)
                    .object(objectName)
                    .build());
            log.info("文件删除成功: bucket={}, object={}", bucketName, objectName);
            return true;
        } catch (Exception e) {
            log.error("文件删除失败: bucket={}, object={}", bucketName, objectName, e);
            return false;
        }
    }

    /**
     * 批量删除文件
     *
     * @param objectNames 对象名称列表
     * @return 删除失败的文件列表
     */
    public List<String> deleteFiles(List<String> objectNames) {
        return deleteFiles(null, objectNames);
    }

    /**
     * 批量删除文件
     *
     * @param bucketName  存储桶名称（为空则使用默认存储桶）
     * @param objectNames 对象名称列表
     * @return 删除失败的文件列表
     */
    public List<String> deleteFiles(String bucketName, List<String> objectNames) {
        if (bucketName == null || bucketName.isEmpty()) {
            bucketName = minioProperties.getBucketName();
        }

        List<DeleteObject> objects = objectNames.stream()
                .map(DeleteObject::new)
                .toList();

        List<String> failedObjects = new ArrayList<>();

        try {
            Iterable<Result<DeleteError>> results = minioClient.removeObjects(
                    RemoveObjectsArgs.builder()
                            .bucket(bucketName)
                            .objects(objects)
                            .build());

            for (Result<DeleteError> result : results) {
                DeleteError error = result.get();
                failedObjects.add(error.objectName());
                log.error("批量删除文件失败: bucket={}, object={}, message={}",
                        bucketName, error.objectName(), error.message());
            }

            if (failedObjects.isEmpty()) {
                log.info("批量删除文件成功: bucket={}, count={}", bucketName, objectNames.size());
            }
        } catch (Exception e) {
            log.error("批量删除文件异常: bucket={}", bucketName, e);
            failedObjects.addAll(objectNames);
        }

        return failedObjects;
    }

    /**
     * 检查文件是否存在
     *
     * @param objectName 对象名称
     * @return 是否存在
     */
    public boolean fileExists(String objectName) {
        return fileExists(null, objectName);
    }

    /**
     * 检查文件是否存在
     *
     * @param bucketName 存储桶名称（为空则使用默认存储桶）
     * @param objectName 对象名称
     * @return 是否存在
     */
    public boolean fileExists(String bucketName, String objectName) {
        if (bucketName == null || bucketName.isEmpty()) {
            bucketName = minioProperties.getBucketName();
        }

        try {
            minioClient.statObject(StatObjectArgs.builder()
                    .bucket(bucketName)
                    .object(objectName)
                    .build());
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * 获取文件访问URL（永久访问）
     *
     * @param objectName 对象名称
     * @return 文件访问URL
     */
    public String getFileUrl(String objectName) {
        return getFileUrl(null, objectName);
    }

    /**
     * 获取文件访问URL（永久访问）
     *
     * @param bucketName 存储桶名称（为空则使用默认存储桶）
     * @param objectName 对象名称
     * @return 文件访问URL
     */
    public String getFileUrl(String bucketName, String objectName) {
        if (bucketName == null || bucketName.isEmpty()) {
            bucketName = minioProperties.getBucketName();
        }

        // 如果配置了文件访问主机，则使用配置的主机
        String fileHost = minioProperties.getFileHost();
        if (fileHost != null && !fileHost.isEmpty()) {
            return String.format("%s/%s/%s", fileHost, bucketName, objectName);
        }

        // 否则使用 endpoint
        return String.format("%s/%s/%s", minioProperties.getEndpoint(), bucketName, objectName);
    }

    /**
     * 获取预签名URL（临时访问）
     *
     * @param objectName 对象名称
     * @param expiry     过期时间（秒）
     * @return 预签名URL
     * @throws Exception 异常
     */
    public String getPresignedUrl(String objectName, int expiry) throws Exception {
        return getPresignedUrl(null, objectName, expiry);
    }

    /**
     * 获取预签名URL（临时访问）
     *
     * @param bucketName 存储桶名称（为空则使用默认存储桶）
     * @param objectName 对象名称
     * @param expiry     过期时间（秒）
     * @return 预签名URL
     * @throws Exception 异常
     */
    public String getPresignedUrl(String bucketName, String objectName, int expiry) throws Exception {
        if (bucketName == null || bucketName.isEmpty()) {
            bucketName = minioProperties.getBucketName();
        }

        return minioClient.getPresignedObjectUrl(GetPresignedObjectUrlArgs.builder()
                .method(Method.GET)
                .bucket(bucketName)
                .object(objectName)
                .expiry(expiry, TimeUnit.SECONDS)
                .build());
    }

    /**
     * 获取文件元数据
     *
     * @param objectName 对象名称
     * @return 文件元数据响应
     * @throws Exception 异常
     */
    public StatObjectResponse getFileInfo(String objectName) throws Exception {
        return getFileInfo(null, objectName);
    }

    /**
     * 获取文件元数据
     *
     * @param bucketName 存储桶名称（为空则使用默认存储桶）
     * @param objectName 对象名称
     * @return 文件元数据响应
     * @throws Exception 异常
     */
    public StatObjectResponse getFileInfo(String bucketName, String objectName) throws Exception {
        if (bucketName == null || bucketName.isEmpty()) {
            bucketName = minioProperties.getBucketName();
        }

        return minioClient.statObject(StatObjectArgs.builder()
                .bucket(bucketName)
                .object(objectName)
                .build());
    }

    /**
     * 列出存储桶中的所有文件
     *
     * @param bucketName 存储桶名称
     * @return 文件列表
     */
    public List<String> listFiles(String bucketName) {
        if (bucketName == null || bucketName.isEmpty()) {
            bucketName = minioProperties.getBucketName();
        }

        List<String> files = new ArrayList<>();
        try {
            Iterable<Result<Item>> results = minioClient.listObjects(
                    ListObjectsArgs.builder()
                            .bucket(bucketName)
                            .recursive(true)
                            .build());

            for (Result<Item> result : results) {
                Item item = result.get();
                files.add(item.objectName());
            }
        } catch (Exception e) {
            log.error("列出文件失败: bucket={}", bucketName, e);
        }

        return files;
    }

    /**
     * 列出存储桶中指定前缀的文件
     *
     * @param bucketName 存储桶名称
     * @param prefix     文件前缀
     * @return 文件列表
     */
    public List<String> listFilesByPrefix(String bucketName, String prefix) {
        if (bucketName == null || bucketName.isEmpty()) {
            bucketName = minioProperties.getBucketName();
        }

        List<String> files = new ArrayList<>();
        try {
            Iterable<Result<Item>> results = minioClient.listObjects(
                    ListObjectsArgs.builder()
                            .bucket(bucketName)
                            .prefix(prefix)
                            .recursive(true)
                            .build());

            for (Result<Item> result : results) {
                Item item = result.get();
                files.add(item.objectName());
            }
        } catch (Exception e) {
            log.error("列出文件失败: bucket={}, prefix={}", bucketName, prefix, e);
        }

        return files;
    }

    /**
     * 生成对象名称
     * 格式: 日期/UUID.扩展名
     *
     * @param originalFilename 原始文件名
     * @return 生成的对象名称
     */
    private String generateObjectName(String originalFilename) {
        String date = LocalDate.now().format(DATE_FORMATTER);
        String uuid = UUID.randomUUID().toString().replace("-", "");

        // 获取文件扩展名
        String extension = "";
        if (originalFilename != null && originalFilename.contains(".")) {
            extension = originalFilename.substring(originalFilename.lastIndexOf("."));
        }

        return String.format("%s/%s%s", date, uuid, extension);
    }
}
