package com.graphrag.gateway.service;

import com.graphrag.common.security.dto.*;
import com.graphrag.gateway.security.LoginUser;

public interface AuthService {

    LoginResponse login(LoginRequest request);

    void register(RegisterRequest request);

    void logout();

    LoginResponse refreshToken(RefreshTokenRequest request);

    UserInfoResponse getCurrentUser();

    LoginUser getLoginUser();

    Long getCurrentUserId();

    String getCurrentUsername();
}
