package com.graphrag.common.cache;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.PropertyAccessor;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.Jackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

import java.time.Duration;
import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * RedisCacheService 测试类
 * 使用 Testcontainers 启动 Redis 容器进行集成测试
 */
@SpringBootTest(classes = RedisCacheServiceTest.TestApplication.class)
@Testcontainers
class RedisCacheServiceTest {

    // Redis 测试容器
    @Container
    @SuppressWarnings("resource")
    static GenericContainer<?> redisContainer = new GenericContainer<>(DockerImageName.parse("redis:7-alpine"))
            .withExposedPorts(6379);

    /**
     * 动态设置 Redis 连接属性
     */
    @DynamicPropertySource
    static void redisProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.data.redis.host", redisContainer::getHost);
        registry.add("spring.data.redis.port", redisContainer::getFirstMappedPort);
    }

    @Autowired
    private RedisCacheService redisCacheService;

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    /**
     * 测试应用配置类
     */
    @SpringBootApplication
    static class TestApplication {

        @Bean
        public RedisConnectionFactory redisConnectionFactory() {
            // 使用 Testcontainers 动态端口
            return new LettuceConnectionFactory(redisContainer.getHost(), redisContainer.getFirstMappedPort());
        }

        @Bean
        public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory connectionFactory) {
            RedisTemplate<String, Object> template = new RedisTemplate<>();
            template.setConnectionFactory(connectionFactory);

            ObjectMapper objectMapper = new ObjectMapper();
            objectMapper.setVisibility(PropertyAccessor.ALL, JsonAutoDetect.Visibility.ANY);
            objectMapper.activateDefaultTyping(objectMapper.getPolymorphicTypeValidator(),
                    ObjectMapper.DefaultTyping.NON_FINAL);
            objectMapper.registerModule(new JavaTimeModule());
            objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

            Jackson2JsonRedisSerializer<Object> jsonSerializer = new Jackson2JsonRedisSerializer<>(objectMapper, Object.class);
            StringRedisSerializer stringSerializer = new StringRedisSerializer();

            template.setKeySerializer(stringSerializer);
            template.setHashKeySerializer(stringSerializer);
            template.setValueSerializer(jsonSerializer);
            template.setHashValueSerializer(jsonSerializer);
            template.afterPropertiesSet();

            return template;
        }

        @Bean
        public RedisCacheService redisCacheService(RedisTemplate<String, Object> redisTemplate) {
            return new RedisCacheService(redisTemplate);
        }
    }

    @BeforeEach
    void setUp() {
        // 清空 Redis 缓存
        redisTemplate.getConnectionFactory().getConnection().flushAll();
    }

    @AfterEach
    void tearDown() {
        // 清空 Redis 缓存
        redisTemplate.getConnectionFactory().getConnection().flushAll();
    }

    @Test
    @DisplayName("测试设置缓存（带过期时间）")
    void testSetWithTimeout() {
        String key = "test:set:timeout";
        String value = "test-value";

        redisCacheService.set(key, value, 300);

        assertTrue(redisCacheService.hasKey(key));
        assertEquals(value, redisCacheService.get(key));
    }

    @Test
    @DisplayName("测试设置缓存（带Duration过期时间）")
    void testSetWithDuration() {
        String key = "test:set:duration";
        String value = "test-value";

        redisCacheService.set(key, value, Duration.ofMinutes(5));

        assertTrue(redisCacheService.hasKey(key));
        assertEquals(value, redisCacheService.get(key));
    }

    @Test
    @DisplayName("测试设置缓存（永不过期）")
    void testSetWithoutTimeout() {
        String key = "test:set:permanent";
        String value = "test-value";

        redisCacheService.set(key, value);

        assertTrue(redisCacheService.hasKey(key));
        assertEquals(value, redisCacheService.get(key));
        assertEquals(-1L, redisCacheService.getExpire(key));
    }

    @Test
    @DisplayName("测试获取缓存")
    void testGet() {
        String key = "test:get";
        String value = "test-value";

        redisCacheService.set(key, value, 300);

        String result = redisCacheService.get(key);
        assertEquals(value, result);
    }

    @Test
    @DisplayName("测试获取不存在的缓存")
    void testGetNonExistent() {
        String key = "test:get:nonexistent";

        String result = redisCacheService.get(key);
        assertNull(result);
    }

    @Test
    @DisplayName("测试删除缓存")
    void testDelete() {
        String key = "test:delete";
        redisCacheService.set(key, "value", 300);

        Boolean result = redisCacheService.delete(key);

        assertTrue(result);
        assertFalse(redisCacheService.hasKey(key));
    }

    @Test
    @DisplayName("测试批量删除缓存")
    void testDeleteBatch() {
        redisCacheService.set("test:delete:1", "value1", 300);
        redisCacheService.set("test:delete:2", "value2", 300);
        redisCacheService.set("test:delete:3", "value3", 300);

        List<String> keys = Arrays.asList("test:delete:1", "test:delete:2", "test:delete:3");
        Long result = redisCacheService.delete(keys);

        assertEquals(3L, result);
        assertFalse(redisCacheService.hasKey("test:delete:1"));
        assertFalse(redisCacheService.hasKey("test:delete:2"));
        assertFalse(redisCacheService.hasKey("test:delete:3"));
    }

    @Test
    @DisplayName("测试检查key是否存在")
    void testHasKey() {
        String key = "test:hasKey";
        redisCacheService.set(key, "value", 300);

        assertTrue(redisCacheService.hasKey(key));
        assertFalse(redisCacheService.hasKey("test:hasKey:nonexistent"));
    }

    @Test
    @DisplayName("测试设置过期时间")
    void testExpire() {
        String key = "test:expire";
        redisCacheService.set(key, "value");

        Boolean result = redisCacheService.expire(key, 600);

        assertTrue(result);
        assertTrue(redisCacheService.getExpire(key) > 0);
    }

    @Test
    @DisplayName("测试设置过期时间（Duration）")
    void testExpireWithDuration() {
        String key = "test:expire:duration";
        redisCacheService.set(key, "value");

        Boolean result = redisCacheService.expire(key, Duration.ofMinutes(10));

        assertTrue(result);
        assertTrue(redisCacheService.getExpire(key) > 0);
    }

    @Test
    @DisplayName("测试获取过期时间")
    void testGetExpire() {
        String key = "test:getExpire";
        redisCacheService.set(key, "value", 300);

        Long expire = redisCacheService.getExpire(key);

        assertTrue(expire > 0 && expire <= 300);
    }

    @Test
    @DisplayName("测试设置Hash缓存")
    void testSetHash() {
        String key = "test:hash:set";
        String hashKey = "field1";
        String value = "value1";

        redisCacheService.setHash(key, hashKey, value);

        assertTrue(redisCacheService.hasHashKey(key, hashKey));
        assertEquals(value, redisCacheService.getHash(key, hashKey));
    }

    @Test
    @DisplayName("测试获取Hash缓存")
    void testGetHash() {
        String key = "test:hash:get";
        String hashKey = "field1";
        String value = "value1";

        redisCacheService.setHash(key, hashKey, value);

        String result = redisCacheService.getHash(key, hashKey);
        assertEquals(value, result);
    }

    @Test
    @DisplayName("测试删除Hash缓存")
    void testDeleteHash() {
        String key = "test:hash:delete";
        redisCacheService.setHash(key, "field1", "value1");
        redisCacheService.setHash(key, "field2", "value2");

        Long result = redisCacheService.deleteHash(key, "field1", "field2");

        assertEquals(2L, result);
        assertFalse(redisCacheService.hasHashKey(key, "field1"));
        assertFalse(redisCacheService.hasHashKey(key, "field2"));
    }

    @Test
    @DisplayName("测试自增操作")
    void testIncrement() {
        String key = "test:increment";

        Long result1 = redisCacheService.increment(key, 5);
        Long result2 = redisCacheService.increment(key, 3);

        assertEquals(5L, result1);
        assertEquals(8L, result2);
    }

    @Test
    @DisplayName("测试自增操作（步长为1）")
    void testIncrementByOne() {
        String key = "test:increment:one";

        Long result1 = redisCacheService.increment(key);
        Long result2 = redisCacheService.increment(key);
        Long result3 = redisCacheService.increment(key);

        assertEquals(1L, result1);
        assertEquals(2L, result2);
        assertEquals(3L, result3);
    }

    @Test
    @DisplayName("测试自减操作")
    void testDecrement() {
        String key = "test:decrement";
        redisCacheService.set(key, 10);

        Long result1 = redisCacheService.decrement(key, 3);
        Long result2 = redisCacheService.decrement(key, 2);

        assertEquals(7L, result1);
        assertEquals(5L, result2);
    }

    @Test
    @DisplayName("测试自减操作（步长为1）")
    void testDecrementByOne() {
        String key = "test:decrement:one";
        redisCacheService.set(key, 5);

        Long result1 = redisCacheService.decrement(key);
        Long result2 = redisCacheService.decrement(key);

        assertEquals(4L, result1);
        assertEquals(3L, result2);
    }

    @Test
    @DisplayName("测试设置缓存（不存在时才设置）- key不存在")
    void testSetIfAbsentKeyNotExists() {
        String key = "test:setIfAbsent:new";
        String value = "value1";

        Boolean result = redisCacheService.setIfAbsent(key, value, 300);

        assertTrue(result);
        assertEquals(value, redisCacheService.get(key));
    }

    @Test
    @DisplayName("测试设置缓存（不存在时才设置）- key已存在")
    void testSetIfAbsentKeyExists() {
        String key = "test:setIfAbsent:exists";
        redisCacheService.set(key, "value1", 300);

        Boolean result = redisCacheService.setIfAbsent(key, "value2", 300);

        assertFalse(result);
        assertEquals("value1", redisCacheService.get(key));
    }

    @Test
    @DisplayName("测试设置缓存（不存在时才设置，使用Duration）")
    void testSetIfAbsentWithDuration() {
        String key = "test:setIfAbsent:duration";
        String value = "value1";

        Boolean result = redisCacheService.setIfAbsent(key, value, Duration.ofMinutes(5));

        assertTrue(result);
        assertEquals(value, redisCacheService.get(key));
    }

    @Test
    @DisplayName("测试设置缓存（存在时才设置）- key存在")
    void testSetIfPresentKeyExists() {
        String key = "test:setIfPresent:exists";
        redisCacheService.set(key, "value1", 300);

        Boolean result = redisCacheService.setIfPresent(key, "value2", 300);

        assertTrue(result);
        assertEquals("value2", redisCacheService.get(key));
    }

    @Test
    @DisplayName("测试设置缓存（存在时才设置）- key不存在")
    void testSetIfPresentKeyNotExists() {
        String key = "test:setIfPresent:new";

        Boolean result = redisCacheService.setIfPresent(key, "value1", 300);

        assertFalse(result);
        assertNull(redisCacheService.get(key));
    }

    @Test
    @DisplayName("测试存储复杂对象")
    void testSetComplexObject() {
        String key = "test:complex:object";
        TestUser user = new TestUser(1L, "张三", "zhangsan@example.com");

        redisCacheService.set(key, user, 300);

        TestUser result = redisCacheService.get(key);
        assertNotNull(result);
        assertEquals(1L, result.id());
        assertEquals("张三", result.name());
        assertEquals("zhangsan@example.com", result.email());
    }

    @Test
    @DisplayName("测试获取原始RedisTemplate")
    void testGetRedisTemplate() {
        RedisTemplate<String, Object> template = redisCacheService.getRedisTemplate();

        assertNotNull(template);
        assertSame(redisTemplate, template);
    }

    /**
     * 测试用户记录类
     */
    record TestUser(Long id, String name, String email) {
    }
}
