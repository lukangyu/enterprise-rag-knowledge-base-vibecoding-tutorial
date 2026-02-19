import React from 'react'
import { Card, Statistic, Progress, Tag, Tooltip } from 'antd'
import {
  FileTextOutlined,
  TeamOutlined,
  DatabaseOutlined,
  SearchOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import './StatCard.css'

interface StatCardProps {
  title: string
  value: number
  icon: React.ReactNode
  suffix?: string
  prefix?: string
  loading?: boolean
  trend?: {
    value: number
    isPositive: boolean
  }
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  suffix,
  prefix,
  loading,
  trend,
}) => {
  return (
    <Card className="stat-card" loading={loading}>
      <div className="stat-card-content">
        <div className="stat-icon">{icon}</div>
        <div className="stat-info">
          <div className="stat-title">{title}</div>
          <div className="stat-value">
            <Statistic
              value={value}
              suffix={suffix}
              prefix={prefix}
              valueStyle={{ fontSize: 28, fontWeight: 600 }}
            />
          </div>
          {trend && (
            <div className={`stat-trend ${trend.isPositive ? 'positive' : 'negative'}`}>
              {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}

interface ComponentStatusCardProps {
  name: string
  status: string
  latency?: number
  message?: string
}

export const ComponentStatusCard: React.FC<ComponentStatusCardProps> = ({
  name,
  status,
  latency,
  message,
}) => {
  const isHealthy = status === 'healthy' || status === 'configured'
  
  return (
    <Card className="component-status-card" size="small">
      <div className="component-status-content">
        <div className="component-name">
          {isHealthy ? (
            <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
          ) : (
            <ExclamationCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
          )}
          {name}
        </div>
        <div className="component-info">
          <Tag color={isHealthy ? 'success' : 'error'}>{status}</Tag>
          {latency && (
            <span className="latency">{latency.toFixed(1)}ms</span>
          )}
        </div>
        {message && (
          <Tooltip title={message}>
            <span className="message">{message.slice(0, 20)}...</span>
          </Tooltip>
        )}
      </div>
    </Card>
  )
}

interface ResourceUsageCardProps {
  cpu: number
  memory: number
  disk: number
  gpu?: number
}

export const ResourceUsageCard: React.FC<ResourceUsageCardProps> = ({
  cpu,
  memory,
  disk,
  gpu,
}) => {
  const getProgressColor = (value: number) => {
    if (value < 60) return '#52c41a'
    if (value < 80) return '#faad14'
    return '#ff4d4f'
  }

  return (
    <Card className="resource-usage-card" title="资源使用">
      <div className="resource-item">
        <span className="resource-label">CPU</span>
        <Progress
          percent={cpu}
          strokeColor={getProgressColor(cpu)}
          size="small"
        />
      </div>
      <div className="resource-item">
        <span className="resource-label">内存</span>
        <Progress
          percent={memory}
          strokeColor={getProgressColor(memory)}
          size="small"
        />
      </div>
      <div className="resource-item">
        <span className="resource-label">磁盘</span>
        <Progress
          percent={disk}
          strokeColor={getProgressColor(disk)}
          size="small"
        />
      </div>
      {gpu !== undefined && (
        <div className="resource-item">
          <span className="resource-label">GPU</span>
          <Progress
            percent={gpu}
            strokeColor={getProgressColor(gpu)}
            size="small"
          />
        </div>
      )}
    </Card>
  )
}

export default StatCard
