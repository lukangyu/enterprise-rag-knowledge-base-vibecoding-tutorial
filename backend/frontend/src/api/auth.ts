import apiClient from './client'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  accessToken: string
  refreshToken: string
  expiresIn: number
  tokenType: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
  phone?: string
  nickname?: string
}

export interface UserInfo {
  id: number
  username: string
  nickname?: string
  email?: string
  phone?: string
  avatar?: string
  status: number
  roles: string[]
  permissions: string[]
  createdAt: string
}

export interface RefreshTokenRequest {
  refreshToken: string
}

export const authApi = {
  async login(request: LoginRequest): Promise<LoginResponse> {
    return apiClient.post<LoginResponse>('/auth/login', request)
  },

  async register(request: RegisterRequest): Promise<void> {
    await apiClient.post('/auth/register', request)
  },

  async logout(): Promise<void> {
    await apiClient.post('/auth/logout')
  },

  async refreshToken(request: RefreshTokenRequest): Promise<LoginResponse> {
    return apiClient.post<LoginResponse>('/auth/refresh', request)
  },

  async getCurrentUser(): Promise<UserInfo> {
    return apiClient.get<UserInfo>('/auth/me')
  },

  async updatePassword(userId: number, data: {
    oldPassword: string
    newPassword: string
  }): Promise<void> {
    await apiClient.put(`/system/user/${userId}/password`, data)
  },
}

export default authApi
