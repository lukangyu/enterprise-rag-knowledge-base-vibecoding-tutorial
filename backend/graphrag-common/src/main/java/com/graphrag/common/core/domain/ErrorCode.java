package com.graphrag.common.core.domain;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
@Schema(description = "错误码枚举")
public enum ErrorCode {

    SUCCESS(200, "操作成功"),
    CREATED(201, "创建成功"),
    ACCEPTED(202, "请求已接受，正在处理"),
    NO_CONTENT(204, "无内容"),

    BAD_REQUEST(400, "请求参数错误"),
    UNAUTHORIZED(401, "未授权，请先登录"),
    FORBIDDEN(403, "无权限访问"),
    NOT_FOUND(404, "资源不存在"),
    METHOD_NOT_ALLOWED(405, "请求方法不允许"),
    CONFLICT(409, "资源冲突"),
    GONE(410, "资源已被删除"),
    UNPROCESSABLE_ENTITY(422, "参数校验失败"),
    TOO_MANY_REQUESTS(429, "请求过于频繁，请稍后重试"),

    INTERNAL_SERVER_ERROR(500, "服务器内部错误"),
    NOT_IMPLEMENTED(501, "功能未实现"),
    BAD_GATEWAY(502, "网关错误"),
    SERVICE_UNAVAILABLE(503, "服务暂不可用"),
    GATEWAY_TIMEOUT(504, "网关超时"),

    USER_NOT_FOUND(1001, "用户不存在"),
    USER_ALREADY_EXISTS(1002, "用户已存在"),
    PASSWORD_ERROR(1003, "密码错误"),
    ACCOUNT_DISABLED(1004, "账号已被禁用"),
    ACCOUNT_LOCKED(1005, "账号已被锁定"),
    TOKEN_EXPIRED(1006, "Token已过期"),
    TOKEN_INVALID(1007, "Token无效"),
    REFRESH_TOKEN_EXPIRED(1008, "刷新Token已过期"),
    OLD_PASSWORD_ERROR(1009, "原密码错误"),
    PASSWORD_NOT_MATCH(1010, "两次密码不一致"),

    DOCUMENT_NOT_FOUND(2001, "文档不存在"),
    DOCUMENT_UPLOAD_FAILED(2002, "文档上传失败"),
    DOCUMENT_PARSE_FAILED(2003, "文档解析失败"),
    DOCUMENT_TYPE_NOT_SUPPORT(2004, "不支持的文档类型"),
    DOCUMENT_SIZE_EXCEEDED(2005, "文档大小超出限制"),
    DOCUMENT_ALREADY_EXISTS(2006, "文档已存在"),
    DOCUMENT_PROCESSING(2007, "文档正在处理中"),
    DOCUMENT_DELETE_FAILED(2008, "文档删除失败"),

    KNOWLEDGE_NOT_FOUND(3001, "知识不存在"),
    ENTITY_EXTRACT_FAILED(3002, "实体抽取失败"),
    RELATION_EXTRACT_FAILED(3003, "关系抽取失败"),
    GRAPH_BUILD_FAILED(3004, "图谱构建失败"),
    VECTORIZE_FAILED(3005, "向量化失败"),
    EMBEDDING_FAILED(3006, "嵌入向量生成失败"),

    SEARCH_FAILED(4001, "检索失败"),
    NO_SEARCH_RESULT(4002, "未找到相关结果"),
    LLM_CALL_FAILED(4003, "LLM调用失败"),
    RERANK_FAILED(4004, "重排序失败"),
    STREAM_ERROR(4005, "流式输出错误"),

    FILE_UPLOAD_FAILED(5001, "文件上传失败"),
    FILE_DELETE_FAILED(5002, "文件删除失败"),
    FILE_NOT_FOUND(5003, "文件不存在"),
    FILE_SIZE_EXCEEDED(5004, "文件大小超出限制"),

    DATABASE_ERROR(6001, "数据库操作失败"),
    CACHE_ERROR(6002, "缓存操作失败"),
    MESSAGE_QUEUE_ERROR(6003, "消息队列操作失败"),
    EXTERNAL_SERVICE_ERROR(6004, "外部服务调用失败");

    private final Integer code;
    private final String message;
}
