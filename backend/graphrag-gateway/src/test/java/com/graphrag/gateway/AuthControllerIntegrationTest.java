package com.graphrag.gateway;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.graphrag.common.security.dto.LoginRequest;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class AuthControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @DisplayName("登录接口测试 - 用户不存在")
    void loginWithNonExistentUser() throws Exception {
        LoginRequest request = new LoginRequest();
        request.setUsername("nonexistent");
        request.setPassword("password123");

        mockMvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(1001));
    }

    @Test
    @DisplayName("刷新令牌接口测试 - 无效令牌")
    void refreshWithInvalidToken() throws Exception {
        String requestBody = "{\"refreshToken\":\"invalid.token.here\"}";

        mockMvc.perform(post("/api/auth/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(requestBody))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(1007));
    }

    @Test
    @DisplayName("获取当前用户信息测试 - 未登录")
    void getCurrentUserWithoutAuth() throws Exception {
        mockMvc.perform(get("/api/auth/me"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("健康检查接口测试")
    void healthCheck() throws Exception {
        mockMvc.perform(get("/api/health"))
                .andExpect(status().isOk());
    }
}
