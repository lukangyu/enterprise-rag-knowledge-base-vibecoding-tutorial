import React, { useState, useRef, useEffect } from 'react'
import { Input, Button, Spin, Empty, Card, Tag, Collapse, Typography, Tooltip } from 'antd'
import { SendOutlined, ClearOutlined, FileTextOutlined, LinkOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useChatStore } from '../../stores/chatStore'
import { chatApi, ChatMessage, SourceReference } from '../../api/chat'
import './ChatInterface.css'

const { TextArea } = Input
const { Panel } = Collapse
const { Text } = Typography

const ChatInterface: React.FC = () => {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const {
    messages,
    sources,
    isLoading,
    isStreaming,
    conversationId,
    error,
    addMessage,
    updateLastMessage,
    setSources,
    setLoading,
    setStreaming,
    setConversationId,
    setError,
    clearMessages,
  } = useChatStore()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    const query = inputValue.trim()
    if (!query || isLoading || isStreaming) return

    setInputValue('')
    setError(null)

    const userMessage: ChatMessage = {
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    }
    addMessage(userMessage)

    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    }
    addMessage(assistantMessage)

    setLoading(true)
    setStreaming(true)

    let fullContent = ''

    try {
      await chatApi.chatStreamPost(
        {
          query,
          conversation_id: conversationId || undefined,
          history: messages.slice(-6),
          top_k: 10,
          use_graph: true,
          use_rerank: true,
          stream: true,
        },
        (data: unknown) => {
          const chunk = data as { type: string; content?: string; source?: SourceReference; done?: boolean }
          
          if (chunk.type === 'text' && chunk.content) {
            fullContent += chunk.content
            updateLastMessage(fullContent)
          } else if (chunk.type === 'source' && chunk.source) {
            setSources([...sources, chunk.source])
          } else if (chunk.type === 'start' && (data as { conversation_id?: string }).conversation_id) {
            setConversationId((data as { conversation_id: string }).conversation_id)
          } else if (chunk.type === 'done') {
            setStreaming(false)
            setLoading(false)
          } else if (chunk.type === 'error') {
            setError((data as { error?: string }).error || 'Unknown error')
            setStreaming(false)
            setLoading(false)
          }
        },
        (error: Error) => {
          setError(error.message)
          setStreaming(false)
          setLoading(false)
        },
        () => {
          setStreaming(false)
          setLoading(false)
        }
      )
    } catch (err) {
      setError((err as Error).message)
      setStreaming(false)
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleClear = () => {
    clearMessages()
    setInputValue('')
  }

  const renderMessage = (message: ChatMessage, index: number) => {
    const isUser = message.role === 'user'

    return (
      <div key={index} className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
        <div className="message-avatar">
          {isUser ? '👤' : '🤖'}
        </div>
        <div className="message-content">
          <div className="message-role">{isUser ? '用户' : '助手'}</div>
          <div className="message-text">
            {isUser ? (
              message.content
            ) : (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content || (isLoading && index === messages.length - 1 ? '思考中...' : '')}
              </ReactMarkdown>
            )}
          </div>
        </div>
      </div>
    )
  }

  const renderSources = () => {
    if (sources.length === 0) return null

    return (
      <div className="sources-panel">
        <Collapse
          defaultActiveKey={['1']}
          ghost
          items={[
            {
              key: '1',
              label: (
                <span className="sources-header">
                  <FileTextOutlined /> 参考来源 ({sources.length})
                </span>
              ),
              children: (
                <div className="sources-list">
                  {sources.map((source, index) => (
                    <Card
                      key={index}
                      size="small"
                      className="source-card"
                      title={
                        <span>
                          <Tag color="blue">{source.source_id}</Tag>
                          <Text ellipsis style={{ maxWidth: 200 }}>
                            {source.doc_id}
                          </Text>
                        </span>
                      }
                    >
                      <Tooltip title={source.content}>
                        <Text ellipsis={{ rows: 3 }}>
                          {source.content}
                        </Text>
                      </Tooltip>
                      <div className="source-meta">
                        <Tag>相关度: {(source.score * 100).toFixed(1)}%</Tag>
                      </div>
                    </Card>
                  ))}
                </div>
              ),
            },
          ]}
        />
      </div>
    )
  }

  return (
    <div className="chat-interface">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <Empty
            description="开始对话"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            className="empty-state"
          />
        ) : (
          <>
            {messages.map(renderMessage)}
            {isStreaming && (
              <div className="streaming-indicator">
                <Spin size="small" />
                <span>正在生成回答...</span>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {renderSources()}

      {error && (
        <div className="error-message">
          <Tag color="error">错误: {error}</Tag>
        </div>
      )}

      <div className="chat-input">
        <TextArea
          ref={inputRef as unknown as React.RefObject<HTMLTextAreaElement>}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入您的问题... (Shift+Enter 换行, Enter 发送)"
          autoSize={{ minRows: 1, maxRows: 4 }}
          disabled={isLoading || isStreaming}
          className="input-textarea"
        />
        <div className="input-actions">
          <Tooltip title="清空对话">
            <Button
              icon={<ClearOutlined />}
              onClick={handleClear}
              disabled={messages.length === 0}
            />
          </Tooltip>
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={isLoading && !isStreaming}
            disabled={!inputValue.trim() || isStreaming}
          >
            发送
          </Button>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface
