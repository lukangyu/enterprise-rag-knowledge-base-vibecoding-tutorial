import React from 'react'
import { Row, Col, Card, Typography } from 'antd'
import { QuestionCircleOutlined, BookOutlined, RocketOutlined } from '@ant-design/icons'
import ChatInterface from '../../components/ChatInterface'
import './Chat.css'

const { Title, Paragraph } = Typography

const features = [
  {
    icon: <QuestionCircleOutlined />,
    title: '智能问答',
    description: '基于知识库的智能问答，支持多轮对话',
  },
  {
    icon: <BookOutlined />,
    title: '知识检索',
    description: '融合向量检索与知识图谱，精准定位信息',
  },
  {
    icon: <RocketOutlined />,
    title: '实时流式输出',
    description: 'SSE流式响应，实时展示生成内容',
  },
]

const ChatPage: React.FC = () => {
  return (
    <Row gutter={24} className="chat-page">
      <Col xs={24} lg={18}>
        <ChatInterface />
      </Col>
      <Col xs={24} lg={6}>
        <Card className="info-card">
          <Title level={4}>GraphRAG 知识库问答</Title>
          <Paragraph type="secondary">
            基于知识图谱和向量检索的智能问答系统，为您提供精准的知识服务。
          </Paragraph>
          <div className="features-list">
            {features.map((feature, index) => (
              <div key={index} className="feature-item">
                <div className="feature-icon">{feature.icon}</div>
                <div className="feature-content">
                  <div className="feature-title">{feature.title}</div>
                  <div className="feature-desc">{feature.description}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </Col>
    </Row>
  )
}

export default ChatPage
