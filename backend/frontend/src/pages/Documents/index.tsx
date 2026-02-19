import React, { useEffect, useState } from 'react'
import {
  Table,
  Card,
  Button,
  Input,
  Space,
  Tag,
  Modal,
  Upload,
  message,
  Popconfirm,
  Select,
  DatePicker,
} from 'antd'
import {
  UploadOutlined,
  DeleteOutlined,
  ReloadOutlined,
  SearchOutlined,
  EyeOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import './Documents.css'

interface Document {
  id: string
  title: string
  doc_type: string
  file_size: number
  status: string
  chunk_count: number
  entity_count: number
  created_at: string
  updated_at: string
}

const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null)

  const fetchDocuments = async () => {
    setLoading(true)
    try {
      setDocuments([
        {
          id: 'doc_001',
          title: '系统设计文档',
          doc_type: 'pdf',
          file_size: 1024000,
          status: 'published',
          chunk_count: 156,
          entity_count: 89,
          created_at: '2026-02-17T10:00:00Z',
          updated_at: '2026-02-17T10:30:00Z',
        },
        {
          id: 'doc_002',
          title: 'API接口文档',
          doc_type: 'md',
          file_size: 512000,
          status: 'published',
          chunk_count: 78,
          entity_count: 45,
          created_at: '2026-02-16T14:00:00Z',
          updated_at: '2026-02-16T14:30:00Z',
        },
        {
          id: 'doc_003',
          title: '用户手册',
          doc_type: 'docx',
          file_size: 2048000,
          status: 'processing',
          chunk_count: 0,
          entity_count: 0,
          created_at: '2026-02-18T09:00:00Z',
          updated_at: '2026-02-18T09:00:00Z',
        },
      ])
    } catch (error) {
      message.error('获取文档列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  const handleDelete = async (id: string) => {
    message.success('文档删除成功')
    fetchDocuments()
  }

  const handleReprocess = async (id: string) => {
    message.success('重新处理任务已提交')
  }

  const handleUpload = async (file: File) => {
    message.success(`文件 ${file.name} 上传成功`)
    setUploadModalVisible(false)
    fetchDocuments()
  }

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      published: { color: 'success', text: '已发布' },
      processing: { color: 'processing', text: '处理中' },
      pending: { color: 'warning', text: '待处理' },
      failed: { color: 'error', text: '失败' },
    }
    const config = statusMap[status] || { color: 'default', text: status }
    return <Tag color={config.color}>{config.text}</Tag>
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const columns: ColumnsType<Document> = [
    {
      title: '文档标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'doc_type',
      key: 'doc_type',
      width: 80,
      render: (type) => <Tag>{type.toUpperCase()}</Tag>,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size) => formatFileSize(size),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => getStatusTag(status),
    },
    {
      title: '分块数',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      width: 80,
    },
    {
      title: '实体数',
      dataIndex: 'entity_count',
      key: 'entity_count',
      width: 80,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedDoc(record)
              setDetailModalVisible(true)
            }}
          >
            查看
          </Button>
          {record.status !== 'processing' && (
            <Button
              type="link"
              size="small"
              icon={<SyncOutlined />}
              onClick={() => handleReprocess(record.id)}
            >
              重处理
            </Button>
          )}
          <Popconfirm
            title="确定删除此文档？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const filteredDocuments = documents.filter((doc) => {
    const matchSearch = doc.title.toLowerCase().includes(searchText.toLowerCase())
    const matchStatus = !statusFilter || doc.status === statusFilter
    return matchSearch && matchStatus
  })

  return (
    <div className="documents-page">
      <Card
        title="文档管理"
        extra={
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={() => setUploadModalVisible(true)}
          >
            上传文档
          </Button>
        }
      >
        <div className="documents-toolbar">
          <Space>
            <Input
              placeholder="搜索文档标题"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 200 }}
            />
            <Select
              placeholder="状态筛选"
              allowClear
              style={{ width: 120 }}
              value={statusFilter}
              onChange={setStatusFilter}
              options={[
                { value: 'published', label: '已发布' },
                { value: 'processing', label: '处理中' },
                { value: 'pending', label: '待处理' },
                { value: 'failed', label: '失败' },
              ]}
            />
            <Button icon={<ReloadOutlined />} onClick={fetchDocuments}>
              刷新
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={filteredDocuments}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      <Modal
        title="上传文档"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
      >
        <Upload.Dragger
          accept=".pdf,.doc,.docx,.md,.txt"
          beforeUpload={(file) => {
            handleUpload(file)
            return false
          }}
          showUploadList={false}
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持 PDF、Word、Markdown、TXT 格式，最大 50MB
          </p>
        </Upload.Dragger>
      </Modal>

      <Modal
        title="文档详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={600}
      >
        {selectedDoc && (
          <div className="document-detail">
            <div className="detail-item">
              <span className="label">文档ID：</span>
              <span>{selectedDoc.id}</span>
            </div>
            <div className="detail-item">
              <span className="label">标题：</span>
              <span>{selectedDoc.title}</span>
            </div>
            <div className="detail-item">
              <span className="label">类型：</span>
              <span>{selectedDoc.doc_type.toUpperCase()}</span>
            </div>
            <div className="detail-item">
              <span className="label">大小：</span>
              <span>{formatFileSize(selectedDoc.file_size)}</span>
            </div>
            <div className="detail-item">
              <span className="label">状态：</span>
              {getStatusTag(selectedDoc.status)}
            </div>
            <div className="detail-item">
              <span className="label">分块数：</span>
              <span>{selectedDoc.chunk_count}</span>
            </div>
            <div className="detail-item">
              <span className="label">实体数：</span>
              <span>{selectedDoc.entity_count}</span>
            </div>
            <div className="detail-item">
              <span className="label">创建时间：</span>
              <span>{dayjs(selectedDoc.created_at).format('YYYY-MM-DD HH:mm:ss')}</span>
            </div>
            <div className="detail-item">
              <span className="label">更新时间：</span>
              <span>{dayjs(selectedDoc.updated_at).format('YYYY-MM-DD HH:mm:ss')}</span>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Documents
