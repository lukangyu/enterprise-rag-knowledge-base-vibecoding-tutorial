package com.graphrag.gateway.service;

import com.graphrag.common.core.domain.PageResult;
import com.graphrag.common.security.dto.*;
import com.graphrag.common.security.entity.User;

import java.util.List;

public interface UserService {

    User createUser(UserCreateRequest request);

    User updateUser(Long id, UserUpdateRequest request);

    void deleteUser(Long id);

    User getUserById(Long id);

    PageResult<User> listUsers(UserQueryRequest request);

    void updatePassword(Long id, PasswordUpdateRequest request);

    void assignRoles(Long id, List<Long> roleIds);

    void updateStatus(Long id, Integer status);

    void resetPassword(Long id);
}
