package com.graphrag.common.cache;

import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Collection;
import java.util.concurrent.TimeUnit;

/**
 * Redis缓存服务工具类
 * 提供统一的Redis缓存操作接口，支持泛型和JSON序列化
 *
 * @author GraphRAG Team
 */
@Service
public class RedisCacheService {

    private final RedisTemplate<String, Object> redisTemplate;

    public RedisCacheService(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    /**
     * 设置缓存（带过期时间）
     *
     * @param key     缓存键
     * @param value   缓存值
     * @param timeout 过期时间（秒）
     */
    public void set(String key, Object value, long timeout) {
        redisTemplate.opsForValue().set(key, value, timeout, TimeUnit.SECONDS);
    }

    /**
     * 设置缓存（带Duration过期时间）
     *
     * @param key      缓存键
     * @param value    缓存值
     * @param duration 过期时间
     */
    public void set(String key, Object value, Duration duration) {
        redisTemplate.opsForValue().set(key, value, duration);
    }

    /**
     * 设置缓存（永不过期）
     *
     * @param key   缓存键
     * @param value 缓存值
     */
    public void set(String key, Object value) {
        redisTemplate.opsForValue().set(key, value);
    }

    /**
     * 获取缓存
     *
     * @param key 缓存键
     * @return 缓存值，不存在则返回null
     */
    @SuppressWarnings("unchecked")
    public <T> T get(String key) {
        return (T) redisTemplate.opsForValue().get(key);
    }

    /**
     * 删除缓存
     *
     * @param key 缓存键
     * @return 是否删除成功
     */
    public Boolean delete(String key) {
        return redisTemplate.delete(key);
    }

    /**
     * 批量删除缓存
     *
     * @param keys 缓存键集合
     * @return 删除的数量
     */
    public Long delete(Collection<String> keys) {
        return redisTemplate.delete(keys);
    }

    /**
     * 检查key是否存在
     *
     * @param key 缓存键
     * @return 是否存在
     */
    public Boolean hasKey(String key) {
        return redisTemplate.hasKey(key);
    }

    /**
     * 设置过期时间
     *
     * @param key     缓存键
     * @param timeout 过期时间（秒）
     * @return 是否设置成功
     */
    public Boolean expire(String key, long timeout) {
        return redisTemplate.expire(key, timeout, TimeUnit.SECONDS);
    }

    /**
     * 设置过期时间（Duration）
     *
     * @param key      缓存键
     * @param duration 过期时间
     * @return 是否设置成功
     */
    public Boolean expire(String key, Duration duration) {
        return redisTemplate.expire(key, duration);
    }

    /**
     * 获取过期时间
     *
     * @param key 缓存键
     * @return 过期时间（秒），-1表示永不过期，-2表示key不存在
     */
    public Long getExpire(String key) {
        return redisTemplate.getExpire(key, TimeUnit.SECONDS);
    }

    /**
     * 设置Hash缓存
     *
     * @param key     缓存键
     * @param hashKey Hash键
     * @param value   缓存值
     */
    public void setHash(String key, String hashKey, Object value) {
        redisTemplate.opsForHash().put(key, hashKey, value);
    }

    /**
     * 获取Hash缓存
     *
     * @param key     缓存键
     * @param hashKey Hash键
     * @return 缓存值
     */
    @SuppressWarnings("unchecked")
    public <T> T getHash(String key, String hashKey) {
        return (T) redisTemplate.opsForHash().get(key, hashKey);
    }

    /**
     * 删除Hash缓存
     *
     * @param key      缓存键
     * @param hashKeys Hash键数组
     * @return 删除的数量
     */
    public Long deleteHash(String key, Object... hashKeys) {
        return redisTemplate.opsForHash().delete(key, hashKeys);
    }

    /**
     * 检查Hash中是否存在指定的hashKey
     *
     * @param key     缓存键
     * @param hashKey Hash键
     * @return 是否存在
     */
    public Boolean hasHashKey(String key, String hashKey) {
        return redisTemplate.opsForHash().hasKey(key, hashKey);
    }

    /**
     * 自增操作
     *
     * @param key   缓存键
     * @param delta 自增步长
     * @return 自增后的值
     */
    public Long increment(String key, long delta) {
        return redisTemplate.opsForValue().increment(key, delta);
    }

    /**
     * 自增操作（步长为1）
     *
     * @param key 缓存键
     * @return 自增后的值
     */
    public Long increment(String key) {
        return increment(key, 1);
    }

    /**
     * 自减操作
     *
     * @param key   缓存键
     * @param delta 自减步长
     * @return 自减后的值
     */
    public Long decrement(String key, long delta) {
        return redisTemplate.opsForValue().decrement(key, delta);
    }

    /**
     * 自减操作（步长为1）
     *
     * @param key 缓存键
     * @return 自减后的值
     */
    public Long decrement(String key) {
        return decrement(key, 1);
    }

    /**
     * 设置缓存（不存在时才设置）
     *
     * @param key     缓存键
     * @param value   缓存值
     * @param timeout 过期时间（秒）
     * @return 是否设置成功（false表示key已存在）
     */
    public Boolean setIfAbsent(String key, Object value, long timeout) {
        return redisTemplate.opsForValue().setIfAbsent(key, value, timeout, TimeUnit.SECONDS);
    }

    /**
     * 设置缓存（不存在时才设置，使用Duration）
     *
     * @param key      缓存键
     * @param value    缓存值
     * @param duration 过期时间
     * @return 是否设置成功（false表示key已存在）
     */
    public Boolean setIfAbsent(String key, Object value, Duration duration) {
        return redisTemplate.opsForValue().setIfAbsent(key, value, duration);
    }

    /**
     * 设置缓存（存在时才设置）
     *
     * @param key     缓存键
     * @param value   缓存值
     * @param timeout 过期时间（秒）
     * @return 是否设置成功（false表示key不存在）
     */
    public Boolean setIfPresent(String key, Object value, long timeout) {
        return redisTemplate.opsForValue().setIfPresent(key, value, timeout, TimeUnit.SECONDS);
    }

    /**
     * 获取原始RedisTemplate
     * 用于执行更复杂的Redis操作
     *
     * @return RedisTemplate实例
     */
    public RedisTemplate<String, Object> getRedisTemplate() {
        return redisTemplate;
    }
}
