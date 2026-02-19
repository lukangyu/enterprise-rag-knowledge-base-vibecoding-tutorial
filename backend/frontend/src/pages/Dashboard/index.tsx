import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Spin, Empty, Typography, Select, Button, message } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import {
  StatCard,
  ComponentStatusCard,
  ResourceUsageCard,
} from '../../components/Dashboard/StatCard'
import { systemApi, SystemStatus, Statistics } from '../../api/system'
import './Dashboard.css'

const { Title } = Typography

const Dashboard: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('7d')

  const fetchData = async () => {
    setLoading(true)
    try {
      const [statusData, statsData] = await Promise.all([
        systemApi.getStatus(),
        systemApi.getStatistics(period),
      ])
      setStatus(statusData)
      setStatistics(statsData)
    } catch (error) {
      message.error('获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [period])

  const handleRefresh = () => {
    fetchData()
  }

  if (loading) {
    return (
      <div className="dashboard-loading">
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <Title level={4}>系统仪表盘</Title>
        <div className="dashboard-actions">
          <Select
            value={period}
            onChange={setPeriod}
            style={{ width: 120, marginRight: 8 }}
            options={[
              { value: '1d', label: '今天' },
              { value: '7d', label: '近7天' },
              { value: '30d', label: '近30天' },
            ]}
          />
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
        </div>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="文档总数"
            value={status?.statistics.total_documents || 0}
            icon={<span>📄</span>}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="实体总数"
            value={status?.statistics.total_entities || 0}
            icon={<span>🔷</span>}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="关系总数"
            value={status?.statistics.total_relations || 0}
            icon={<span>🔗</span>}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="今日查询"
            value={status?.statistics.queries_today || 0}
            icon={<span>🔍</span>}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="组件状态" className="dashboard-card">
            {status?.components.map((comp) => (
              <ComponentStatusCard
                key={comp.name}
                name={comp.name}
                status={comp.status}
                latency={comp.latency_ms}
                message={comp.message}
              />
            ))}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <ResourceUsageCard
            cpu={status?.resources.cpu_usage || 0}
            memory={status?.resources.memory_usage || 0}
            disk={status?.resources.disk_usage || 0}
            gpu={status?.resources.gpu_usage}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="文档统计" className="dashboard-card">
            {statistics?.document_stats ? (
              <div className="stats-list">
                <div className="stats-item">
                  <span>总文档数</span>
                  <span>{statistics.document_stats.total}</span>
                </div>
                <div className="stats-item">
                  <span>本周期新增</span>
                  <span>{statistics.document_stats.new_this_period}</span>
                </div>
                <div className="stats-divider">按类型分布</div>
                {Object.entries(statistics.document_stats.by_type).map(([type, count]) => (
                  <div key={type} className="stats-item">
                    <span>{type.toUpperCase()}</span>
                    <span>{count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="查询统计" className="dashboard-card">
            {statistics?.query_stats ? (
              <div className="stats-list">
                <div className="stats-item">
                  <span>总查询数</span>
                  <span>{statistics.query_stats.total_queries}</span>
                </div>
                <div className="stats-item">
                  <span>平均响应时间</span>
                  <span>{statistics.query_stats.avg_response_time_ms.toFixed(0)}ms</span>
                </div>
                <div className="stats-item">
                  <span>平均满意度</span>
                  <span>{statistics.query_stats.avg_satisfaction.toFixed(1)}/5</span>
                </div>
              </div>
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="知识图谱统计" className="dashboard-card">
            {statistics?.kg_stats ? (
              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <div className="stats-list">
                    <div className="stats-divider">实体类型分布</div>
                    {Object.entries(statistics.kg_stats.entity_types).map(([type, count]) => (
                      <div key={type} className="stats-item">
                        <span>{type}</span>
                        <span>{count}</span>
                      </div>
                    ))}
                  </div>
                </Col>
                <Col xs={24} sm={12}>
                  <div className="stats-list">
                    <div className="stats-divider">关系类型分布</div>
                    {Object.entries(statistics.kg_stats.relation_types).map(([type, count]) => (
                      <div key={type} className="stats-item">
                        <span>{type}</span>
                        <span>{count}</span>
                      </div>
                    ))}
                  </div>
                </Col>
              </Row>
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
