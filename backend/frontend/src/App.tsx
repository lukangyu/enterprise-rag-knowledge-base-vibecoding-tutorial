import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  MessageOutlined,
  DashboardOutlined,
  FileTextOutlined,
  TeamOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import ChatPage from './pages/Chat'
import Dashboard from './pages/Dashboard'
import Documents from './pages/Documents'
import Users from './pages/Users'
import Settings from './pages/Settings'
import './App.css'

const { Header, Content, Sider, Footer } = Layout

const menuItems = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: <Link to="/dashboard">仪表盘</Link>,
  },
  {
    key: '/chat',
    icon: <MessageOutlined />,
    label: <Link to="/chat">问答对话</Link>,
  },
  {
    key: '/documents',
    icon: <FileTextOutlined />,
    label: <Link to="/documents">文档管理</Link>,
  },
  {
    key: '/users',
    icon: <TeamOutlined />,
    label: <Link to="/users">用户管理</Link>,
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: <Link to="/settings">系统配置</Link>,
  },
]

const AppContent: React.FC = () => {
  const location = useLocation()

  return (
    <Layout className="layout">
      <Sider width={200} className="sider">
        <div className="logo">
          <span className="logo-icon">📚</span>
          <span className="logo-text">GraphRAG</span>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          className="sider-menu"
        />
      </Sider>
      <Layout>
        <Header className="header">
          <div className="header-title">GraphRAG 知识库系统</div>
        </Header>
        <Content className="content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/users" element={<Users />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Content>
        <Footer className="footer">
          GraphRAG Knowledge Base System ©2024
        </Footer>
      </Layout>
    </Layout>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}

export default App
