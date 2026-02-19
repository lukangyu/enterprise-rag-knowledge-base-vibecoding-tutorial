import React, { useEffect, useState } from 'react'
import {
  Table,
  Card,
  Button,
  Input,
  Space,
  Tag,
  Modal,
  Form,
  Select,
  message,
  Popconfirm,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import './Users.css'

interface User {
  id: string
  username: string
  name: string
  email: string
  department: string
  roles: string[]
  status: string
  last_login: string
  created_at: string
}

const Users: React.FC = () => {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [modalVisible, setModalVisible] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [form] = Form.useForm()

  const fetchUsers = async () => {
    setLoading(true)
    try {
      setUsers([
        {
          id: 'user_001',
          username: 'admin',
          name: '管理员',
          email: 'admin@example.com',
          department: '技术部',
          roles: ['admin'],
          status: 'active',
          last_login: '2026-02-17T09:00:00Z',
          created_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 'user_002',
          username: 'zhangsan',
          name: '张三',
          email: 'zhangsan@example.com',
          department: '技术部',
          roles: ['user'],
          status: 'active',
          last_login: '2026-02-16T14:00:00Z',
          created_at: '2025-06-15T00:00:00Z',
        },
      ])
    } catch (error) {
      message.error('获取用户列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  const handleCreate = () => {
    setEditingUser(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (user: User) => {
    setEditingUser(user)
    form.setFieldsValue({
      ...user,
      roles: user.roles,
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    message.success('用户删除成功')
    fetchUsers()
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingUser) {
        message.success('用户更新成功')
      } else {
        message.success('用户创建成功')
      }
      setModalVisible(false)
      fetchUsers()
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const columns: ColumnsType<User> = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
    },
    {
      title: '角色',
      dataIndex: 'roles',
      key: 'roles',
      render: (roles: string[]) => (
        <>
          {roles.map((role) => (
            <Tag key={role} color={role === 'admin' ? 'red' : 'blue'}>
              {role === 'admin' ? '管理员' : '用户'}
            </Tag>
          ))}
        </>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'active' ? 'success' : 'default'}>
          {status === 'active' ? '正常' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date) => (date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '-'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此用户？"
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

  const filteredUsers = users.filter(
    (user) =>
      user.username.toLowerCase().includes(searchText.toLowerCase()) ||
      user.name.toLowerCase().includes(searchText.toLowerCase())
  )

  return (
    <div className="users-page">
      <Card
        title="用户管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建用户
          </Button>
        }
      >
        <div className="users-toolbar">
          <Input
            placeholder="搜索用户名或姓名"
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
          />
        </div>

        <Table
          columns={columns}
          dataSource={filteredUsers}
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
        title={editingUser ? '编辑用户' : '新建用户'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input disabled={!!editingUser} />
          </Form.Item>
          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="department" label="部门">
            <Input />
          </Form.Item>
          <Form.Item
            name="roles"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select
              mode="multiple"
              options={[
                { value: 'admin', label: '管理员' },
                { value: 'user', label: '普通用户' },
                { value: 'knowledge_mgr', label: '知识管理员' },
              ]}
            />
          </Form.Item>
          <Form.Item name="status" label="状态" initialValue="active">
            <Select
              options={[
                { value: 'active', label: '正常' },
                { value: 'disabled', label: '禁用' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Users
