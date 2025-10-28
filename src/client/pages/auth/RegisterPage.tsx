import { isAxiosError } from 'axios'
import {
  Alert,
  App,
  Button,
  Card,
  Flex,
  Form,
  Input,
  Space,
  Spin,
  Typography,
} from 'antd'
import {
  LockOutlined,
  MailOutlined,
  UserAddOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

function resolveErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const payload = error.response?.data as { detail?: string; message?: string } | undefined
    return payload?.detail ?? payload?.message ?? '注册失败，请稍后再试。'
  }
  if (error instanceof Error) {
    return error.message
  }
  return '注册失败，请稍后再试。'
}

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register, loading, isAuthenticated } = useAuth()
  const { message } = App.useApp()

  const [form] = Form.useForm<{ username: string; email: string; password: string }>()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, loading, navigate])

  const handleSubmit = async (values: { username: string; email: string; password: string }) => {
    setSubmitting(true)
    setError(null)
    setSuccessMessage(null)
    try {
      await register(values)
      setSuccessMessage('注册成功，请使用新账号登录。')
      message.success('注册成功')
      form.resetFields()
    } catch (err) {
      const text = resolveErrorMessage(err)
      setError(text)
      message.error(text)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <Flex
        align="center"
        justify="center"
        style={{ minHeight: '100vh' }}
      >
        <Spin tip="正在加载，请稍候" size="large" />
      </Flex>
    )
  }

  return (
    <Flex
      align="center"
      justify="center"
      style={{ minHeight: '100vh', padding: '48px 16px' }}
    >
      <Card
        bordered={false}
        style={{ width: '100%', maxWidth: 420, boxShadow: '0 16px 40px rgba(15, 23, 42, 0.12)' }}
      >
        <Space direction="vertical" size={24} style={{ width: '100%' }}>
          <div>
            <Typography.Title level={3} style={{ marginBottom: 8 }}>
              创建新账号
            </Typography.Title>
            <Typography.Text type="secondary">
              填写基础信息即可体验最新版本的前端模板能力。
            </Typography.Text>
          </div>
          {error && <Alert type="error" showIcon message={error} />}
          {successMessage && <Alert type="success" showIcon message={successMessage} />}
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            requiredMark={false}
            autoComplete="on"
          >
            <Form.Item
              label="用户名"
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少 3 个字符' },
              ]}
            >
              <Input
                size="large"
                prefix={<UserOutlined />}
                placeholder="请输入用户名"
                autoComplete="username"
                allowClear
              />
            </Form.Item>
            <Form.Item
              label="邮箱"
              name="email"
              rules={[
                { required: true, message: '请输入邮箱地址' },
                { type: 'email', message: '请输入正确的邮箱格式' },
              ]}
            >
              <Input
                size="large"
                prefix={<MailOutlined />}
                placeholder="请输入邮箱地址"
                autoComplete="email"
                allowClear
              />
            </Form.Item>
            <Form.Item
              label="密码"
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 8, message: '密码至少 8 个字符' },
              ]}
            >
              <Input.Password
                size="large"
                prefix={<LockOutlined />}
                placeholder="请输入密码"
                autoComplete="new-password"
              />
            </Form.Item>
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                icon={<UserAddOutlined />}
                loading={submitting}
                block
              >
                注册
              </Button>
            </Form.Item>
          </Form>
          <Flex justify="center" gap={8}>
            <Typography.Text type="secondary">已有账号？</Typography.Text>
            <Link to="/login" className="font-medium text-sky-600">
              返回登录
            </Link>
          </Flex>
        </Space>
      </Card>
    </Flex>
  )
}
