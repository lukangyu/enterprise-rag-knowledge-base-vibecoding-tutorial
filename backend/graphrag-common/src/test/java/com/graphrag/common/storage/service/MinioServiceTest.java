package com.graphrag.common.storage.service;

import com.graphrag.common.storage.config.MinioProperties;
import io.minio.GetObjectResponse;
import io.minio.MinioClient;
import io.minio.StatObjectResponse;
import io.minio.messages.Bucket;
import io.minio.messages.Item;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.time.ZonedDateTime;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * MinioService 测试类
 * 测试文件上传、下载、删除、检查等功能
 *
 * @author GraphRAG Team
 */
@ExtendWith(MockitoExtension.class)
class MinioServiceTest {

    @Mock
    private MinioClient minioClient;

    private MinioProperties minioProperties;
    private MinioService minioService;

    @BeforeEach
    void setUp() {
        // 创建配置属性
        minioProperties = new MinioProperties();
        minioProperties.setEndpoint("http://localhost:9000");
        minioProperties.setAccessKey("minioadmin");
        minioProperties.setSecretKey("minioadmin");
        minioProperties.setBucketName("test-bucket");
        minioProperties.setAutoCreateBucket(true);
        minioProperties.setConnectTimeout(10);
        minioProperties.setWriteTimeout(60);
        minioProperties.setReadTimeout(60);

        // 创建服务实例
        minioService = new MinioService(minioClient, minioProperties);
    }

    @Test
    @DisplayName("测试检查存储桶是否存在 - 存在的情况")
    void testBucketExists_True() throws Exception {
        // 模拟存储桶存在
        when(minioClient.bucketExists(any())).thenReturn(true);

        boolean result = minioService.bucketExists("test-bucket");

        assertTrue(result);
        verify(minioClient, times(1)).bucketExists(any());
    }

    @Test
    @DisplayName("测试检查存储桶是否存在 - 不存在的情况")
    void testBucketExists_False() throws Exception {
        // 模拟存储桶不存在
        when(minioClient.bucketExists(any())).thenReturn(false);

        boolean result = minioService.bucketExists("non-existent-bucket");

        assertFalse(result);
        verify(minioClient, times(1)).bucketExists(any());
    }

    @Test
    @DisplayName("测试检查存储桶是否存在 - 异常情况")
    void testBucketExists_Exception() throws Exception {
        // 模拟异常
        when(minioClient.bucketExists(any())).thenThrow(new RuntimeException("连接失败"));

        boolean result = minioService.bucketExists("test-bucket");

        assertFalse(result);
    }

    @Test
    @DisplayName("测试创建存储桶 - 成功")
    void testCreateBucket_Success() throws Exception {
        // 模拟创建成功
        doNothing().when(minioClient).makeBucket(any());

        boolean result = minioService.createBucket("new-bucket");

        assertTrue(result);
        verify(minioClient, times(1)).makeBucket(any());
    }

    @Test
    @DisplayName("测试创建存储桶 - 失败")
    void testCreateBucket_Failure() throws Exception {
        // 模拟创建失败
        doThrow(new RuntimeException("创建失败")).when(minioClient).makeBucket(any());

        boolean result = minioService.createBucket("new-bucket");

        assertFalse(result);
    }

    @Test
    @DisplayName("测试删除存储桶 - 成功")
    void testDeleteBucket_Success() throws Exception {
        // 模拟删除成功
        doNothing().when(minioClient).removeBucket(any());

        boolean result = minioService.deleteBucket("test-bucket");

        assertTrue(result);
        verify(minioClient, times(1)).removeBucket(any());
    }

    @Test
    @DisplayName("测试删除存储桶 - 失败")
    void testDeleteBucket_Failure() throws Exception {
        // 模拟删除失败
        doThrow(new RuntimeException("删除失败")).when(minioClient).removeBucket(any());

        boolean result = minioService.deleteBucket("test-bucket");

        assertFalse(result);
    }

    @Test
    @DisplayName("测试上传文件 - 使用默认存储桶")
    void testUploadFile_DefaultBucket() throws Exception {
        // 准备测试数据
        MockMultipartFile file = new MockMultipartFile(
                "file",
                "test.txt",
                "text/plain",
                "Hello, MinIO!".getBytes()
        );

        // 模拟存储桶存在
        when(minioClient.bucketExists(any())).thenReturn(true);
        // 模拟上传成功
        when(minioClient.putObject(any())).thenReturn(null);

        String result = minioService.uploadFile(file);

        assertNotNull(result);
        assertTrue(result.contains("test-bucket"));
        verify(minioClient, times(1)).putObject(any());
    }

    @Test
    @DisplayName("测试上传文件 - 指定存储桶")
    void testUploadFile_SpecifiedBucket() throws Exception {
        // 准备测试数据
        MockMultipartFile file = new MockMultipartFile(
                "file",
                "test.txt",
                "text/plain",
                "Hello, MinIO!".getBytes()
        );

        // 模拟存储桶不存在，需要创建
        when(minioClient.bucketExists(any())).thenReturn(false);
        doNothing().when(minioClient).makeBucket(any());
        when(minioClient.putObject(any())).thenReturn(null);

        String result = minioService.uploadFile(file, "custom-bucket", "custom/path/test.txt");

        assertNotNull(result);
        assertTrue(result.contains("custom-bucket"));
        assertTrue(result.contains("custom/path/test.txt"));
        verify(minioClient, times(1)).makeBucket(any());
        verify(minioClient, times(1)).putObject(any());
    }

    @Test
    @DisplayName("测试上传文件 - 通过输入流")
    void testUploadFile_InputStream() throws Exception {
        // 准备测试数据
        InputStream inputStream = new ByteArrayInputStream("Hello, MinIO!".getBytes());

        // 模拟存储桶存在
        when(minioClient.bucketExists(any())).thenReturn(true);
        when(minioClient.putObject(any())).thenReturn(null);

        String result = minioService.uploadFile(inputStream, "test-bucket", "test.txt", "text/plain", 13);

        assertNotNull(result);
        assertTrue(result.contains("test-bucket"));
        assertTrue(result.contains("test.txt"));
    }

    @Test
    @DisplayName("测试下载文件")
    void testDownloadFile() throws Exception {
        // 准备测试数据
        InputStream mockInputStream = new ByteArrayInputStream("Hello, MinIO!".getBytes());

        // 模拟下载响应
        GetObjectResponse mockResponse = mock(GetObjectResponse.class);
        when(minioClient.getObject(any())).thenReturn(mockResponse);

        InputStream result = minioService.downloadFile("test.txt");

        assertNotNull(result);
        verify(minioClient, times(1)).getObject(any());
    }

    @Test
    @DisplayName("测试删除文件 - 成功")
    void testDeleteFile_Success() throws Exception {
        // 模拟删除成功
        doNothing().when(minioClient).removeObject(any());

        boolean result = minioService.deleteFile("test.txt");

        assertTrue(result);
        verify(minioClient, times(1)).removeObject(any());
    }

    @Test
    @DisplayName("测试删除文件 - 失败")
    void testDeleteFile_Failure() throws Exception {
        // 模拟删除失败
        doThrow(new RuntimeException("删除失败")).when(minioClient).removeObject(any());

        boolean result = minioService.deleteFile("test.txt");

        assertFalse(result);
    }

    @Test
    @DisplayName("测试批量删除文件")
    void testDeleteFiles() throws Exception {
        // 模拟批量删除返回空结果（全部成功）
        when(minioClient.removeObjects(any())).thenReturn(Collections.emptyList());

        List<String> objectNames = Arrays.asList("file1.txt", "file2.txt", "file3.txt");
        List<String> failedObjects = minioService.deleteFiles(objectNames);

        assertTrue(failedObjects.isEmpty());
    }

    @Test
    @DisplayName("测试检查文件是否存在 - 存在")
    void testFileExists_True() throws Exception {
        // 模拟文件存在
        when(minioClient.statObject(any())).thenReturn(mock(StatObjectResponse.class));

        boolean result = minioService.fileExists("test.txt");

        assertTrue(result);
    }

    @Test
    @DisplayName("测试检查文件是否存在 - 不存在")
    void testFileExists_False() throws Exception {
        // 模拟文件不存在
        when(minioClient.statObject(any())).thenThrow(new RuntimeException("文件不存在"));

        boolean result = minioService.fileExists("non-existent.txt");

        assertFalse(result);
    }

    @Test
    @DisplayName("测试获取文件URL - 默认存储桶")
    void testGetFileUrl_DefaultBucket() {
        String result = minioService.getFileUrl("test.txt");

        assertNotNull(result);
        assertEquals("http://localhost:9000/test-bucket/test.txt", result);
    }

    @Test
    @DisplayName("测试获取文件URL - 指定存储桶")
    void testGetFileUrl_SpecifiedBucket() {
        String result = minioService.getFileUrl("custom-bucket", "path/to/file.txt");

        assertNotNull(result);
        assertEquals("http://localhost:9000/custom-bucket/path/to/file.txt", result);
    }

    @Test
    @DisplayName("测试获取文件URL - 使用自定义文件主机")
    void testGetFileUrl_CustomFileHost() {
        // 设置自定义文件主机
        minioProperties.setFileHost("http://cdn.example.com");

        String result = minioService.getFileUrl("test.txt");

        assertNotNull(result);
        assertEquals("http://cdn.example.com/test-bucket/test.txt", result);
    }

    @Test
    @DisplayName("测试获取预签名URL")
    void testGetPresignedUrl() throws Exception {
        // 模拟预签名URL生成
        when(minioClient.getPresignedObjectUrl(any())).thenReturn("http://localhost:9000/test-bucket/test.txt?signature=xxx");

        String result = minioService.getPresignedUrl("test.txt", 3600);

        assertNotNull(result);
        assertTrue(result.contains("signature"));
    }

    @Test
    @DisplayName("测试获取文件信息")
    void testGetFileInfo() throws Exception {
        // 模拟文件信息响应
        StatObjectResponse mockResponse = mock(StatObjectResponse.class);
        when(mockResponse.bucket()).thenReturn("test-bucket");
        when(mockResponse.object()).thenReturn("test.txt");
        when(mockResponse.size()).thenReturn(13L);
        when(mockResponse.contentType()).thenReturn("text/plain");
        when(minioClient.statObject(any())).thenReturn(mockResponse);

        StatObjectResponse result = minioService.getFileInfo("test.txt");

        assertNotNull(result);
        assertEquals("test-bucket", result.bucket());
        assertEquals("test.txt", result.object());
        assertEquals(13L, result.size());
        assertEquals("text/plain", result.contentType());
    }

    @Test
    @DisplayName("测试列出存储桶中的所有文件")
    void testListFiles() throws Exception {
        // 模拟文件列表
        when(minioClient.listObjects(any())).thenReturn(Collections.emptyList());

        List<String> result = minioService.listFiles("test-bucket");

        assertNotNull(result);
    }

    @Test
    @DisplayName("测试列出指定前缀的文件")
    void testListFilesByPrefix() throws Exception {
        // 模拟文件列表
        when(minioClient.listObjects(any())).thenReturn(Collections.emptyList());

        List<String> result = minioService.listFilesByPrefix("test-bucket", "documents/");

        assertNotNull(result);
    }

    @Test
    @DisplayName("测试初始化默认存储桶 - 存储桶已存在")
    void testInitDefaultBucket_Exists() throws Exception {
        // 模拟存储桶已存在
        when(minioClient.bucketExists(any())).thenReturn(true);

        minioService.initDefaultBucket();

        // 验证没有创建新存储桶
        verify(minioClient, never()).makeBucket(any());
    }

    @Test
    @DisplayName("测试初始化默认存储桶 - 存储桶不存在")
    void testInitDefaultBucket_NotExists() throws Exception {
        // 模拟存储桶不存在
        when(minioClient.bucketExists(any())).thenReturn(false);
        doNothing().when(minioClient).makeBucket(any());

        minioService.initDefaultBucket();

        // 验证创建了新存储桶
        verify(minioClient, times(1)).makeBucket(any());
    }

    @Test
    @DisplayName("测试初始化默认存储桶 - 禁用自动创建")
    void testInitDefaultBucket_Disabled() throws Exception {
        // 禁用自动创建
        minioProperties.setAutoCreateBucket(false);

        minioService.initDefaultBucket();

        // 验证没有检查存储桶
        verify(minioClient, never()).bucketExists(any());
    }
}
