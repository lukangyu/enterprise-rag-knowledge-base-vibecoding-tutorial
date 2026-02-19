import React, { useEffect, useState } from 'react'
import {
  Card,
  Form,
  Input,
  InputNumber,
  Switch,
  Button,
  Divider,
  message,
  Spin,
  Space,
} from 'antd'
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons'
import { systemApi, SystemConfig } from '../../api/system'
import './Settings.css'

const Settings: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const fetchConfig = async () => {
    setLoading(true)
    try {
      const config = await systemApi.getConfig()
      form.setFieldsValue(config)
    } catch (error) {
      message.error('获取配置失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConfig()
  }, [])

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)
      await systemApi.updateConfig(values)
      message.success('配置保存成功')
    } catch (error) {
      message.error('配置保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    fetchConfig()
    message.info('配置已重置')
  }

  if (loading) {
    return (
      <div className="settings-loading">
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div className="settings-page">
      <Card
        title="系统配置"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={handleReset}>
              重置
            </Button>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              loading={saving}
              onClick={handleSave}
            >
              保存配置
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          <Divider orientation="left">基本设置</Divider>

          <Form.Item name={['general', 'site_name']} label="站点名称">
            <Input />
          </Form.Item>

          <Form.Item name={['general', 'site_description']} label="站点描述">
            <Input.TextArea rows={2} />
          </Form.Item>

          <Form.Item
            name={['general', 'max_upload_size']}
            label="最大上传大小（字节）"
          >
            <InputNumber min={1048576} max={104857600} style={{ width: '100%' }} />
          </Form.Item>

          <Divider orientation="left">检索设置</Divider>

          <Form.Item name={['search', 'default_top_k']} label="默认返回数量">
            <InputNumber min={1} max={100} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name={['search', 'max_top_k']} label="最大返回数量">
            <InputNumber min={10} max={1000} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name={['search', 'default_threshold']}
            label="默认相似度阈值"
          >
            <InputNumber
              min={0}
              max={1}
              step={0.1}
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item
            name={['search', 'enable_hybrid_search']}
            label="启用混合检索"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Divider orientation="left">LLM设置</Divider>

          <Form.Item name={['llm', 'default_model']} label="默认模型">
            <Input />
          </Form.Item>

          <Form.Item name={['llm', 'max_tokens']} label="最大Token数">
            <InputNumber min={256} max={8192} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name={['llm', 'default_temperature']}
            label="默认温度"
          >
            <InputNumber
              min={0}
              max={1}
              step={0.1}
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Divider orientation="left">知识图谱设置</Divider>

          <Form.Item name={['kg', 'default_max_hops']} label="默认最大跳数">
            <InputNumber min={1} max={5} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name={['kg', 'default_min_confidence']}
            label="默认最小置信度"
          >
            <InputNumber
              min={0}
              max={1}
              step={0.1}
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item
            name={['kg', 'enable_auto_extraction']}
            label="启用自动抽取"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Settings
