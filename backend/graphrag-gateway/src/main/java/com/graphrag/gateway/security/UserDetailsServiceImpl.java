package com.graphrag.gateway.security;

import com.graphrag.common.security.entity.User;
import com.graphrag.gateway.mapper.UserMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserDetailsServiceImpl implements UserDetailsService {

    private final UserMapper userMapper;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        User user = userMapper.selectByUsername(username);
        if (user == null) {
            throw new UsernameNotFoundException("User not found: " + username);
        }

        List<String> roleCodes = userMapper.selectRoleCodesByUserId(user.getId());
        List<String> permissions = userMapper.selectPermissionCodesByUserId(user.getId());

        LoginUser loginUser = new LoginUser();
        loginUser.setUserId(user.getId());
        loginUser.setUsername(user.getUsername());
        loginUser.setPassword(user.getPassword());
        loginUser.setStatus(user.getStatus());
        loginUser.setRoleCodes(roleCodes);
        loginUser.setPermissions(permissions);

        log.debug("Loaded user: {}, roles: {}, permissions: {}", username, roleCodes, permissions);
        return loginUser;
    }

    public LoginUser loadUserById(Long userId) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            return null;
        }

        List<String> roleCodes = userMapper.selectRoleCodesByUserId(user.getId());
        List<String> permissions = userMapper.selectPermissionCodesByUserId(user.getId());

        LoginUser loginUser = new LoginUser();
        loginUser.setUserId(user.getId());
        loginUser.setUsername(user.getUsername());
        loginUser.setPassword(user.getPassword());
        loginUser.setStatus(user.getStatus());
        loginUser.setRoleCodes(roleCodes);
        loginUser.setPermissions(permissions);

        return loginUser;
    }
}
