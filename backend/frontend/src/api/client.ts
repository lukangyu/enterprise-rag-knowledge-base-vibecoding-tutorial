import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const REQUEST_TIMEOUT = 30000

interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

interface PaginationParams {
  page?: number
  size?: number
}

interface PaginationResponse<T> {
  items: T[]
  pagination: {
    page: number
    size: number
    total: number
    total_pages: number
  }
}

class ApiClient {
  private instance: AxiosInstance

  constructor() {
    this.instance = axios.create({
      baseURL: API_BASE_URL,
      timeout: REQUEST_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors(): void {
    this.instance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    this.instance.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        const { data } = response
        if (data.code && data.code !== 200 && data.code !== 201) {
          return Promise.reject(new Error(data.message || 'Request failed'))
        }
        return response
      },
      (error: AxiosError<ApiResponse>) => {
        if (error.response) {
          const { status, data } = error.response
          
          switch (status) {
            case 401:
              localStorage.removeItem('token')
              window.location.href = '/login'
              break
            case 403:
              console.error('Permission denied')
              break
            case 404:
              console.error('Resource not found')
              break
            case 500:
              console.error('Server error')
              break
          }
          
          return Promise.reject(new Error(data?.message || `HTTP Error: ${status}`))
        }
        
        if (error.request) {
          return Promise.reject(new Error('Network error - no response received'))
        }
        
        return Promise.reject(error)
      }
    )
  }

  async get<T = unknown>(
    url: string,
    params?: Record<string, unknown>,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.instance.get<ApiResponse<T>>(url, {
      params,
      ...config,
    })
    return response.data.data
  }

  async post<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.instance.post<ApiResponse<T>>(url, data, config)
    return response.data.data
  }

  async put<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.instance.put<ApiResponse<T>>(url, data, config)
    return response.data.data
  }

  async patch<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.instance.patch<ApiResponse<T>>(url, data, config)
    return response.data.data
  }

  async delete<T = unknown>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.instance.delete<ApiResponse<T>>(url, config)
    return response.data.data
  }

  async getPaged<T = unknown>(
    url: string,
    params?: PaginationParams & Record<string, unknown>
  ): Promise<PaginationResponse<T>> {
    const response = await this.instance.get<ApiResponse<PaginationResponse<T>>>(url, {
      params,
    })
    return response.data.data
  }

  setBaseUrl(baseUrl: string): void {
    this.instance.defaults.baseURL = baseUrl
  }

  setToken(token: string): void {
    this.instance.defaults.headers.common['Authorization'] = `Bearer ${token}`
    localStorage.setItem('token', token)
  }

  clearToken(): void {
    delete this.instance.defaults.headers.common['Authorization']
    localStorage.removeItem('token')
  }
}

export const apiClient = new ApiClient()

export default apiClient
