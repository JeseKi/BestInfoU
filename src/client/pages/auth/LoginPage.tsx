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
  LoginOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

function resolveErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const payload = error.response?.data as { detail?: string; message?: string } | undefined
    return payload?.detail ?? payload?.message ?? '登录失败，请稍后重试。'
  }
  if (error instanceof Error) {
    return error.message
  }
  return '登录失败，请稍后重试。'
}

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, loading, isAuthenticated } = useAuth()
  const { message } = App.useApp()

  const [form] = Form.useForm<{ username: string; password: string }>()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, loading, navigate])

  const handleSubmit = async (values: { username: string; password: string }) => {
    console.log('【登录页面】提交数据', { 用户名: values.username })
    setSubmitting(true)
    setError(null)
    try {
      await login(values)
      const fromState = location.state as { from?: { pathname?: string } } | undefined
      const redirectPath = fromState?.from?.pathname ?? '/'
      message.success('欢迎回来')
      navigate(redirectPath, { replace: true })
    } catch (err) {
      console.error('【登录页面】调用登录接口失败', err)
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
        <Spin tip="正在验证登录状态" size="large" />
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
              欢迎回来
            </Typography.Title>
            <Typography.Text type="secondary">
              输入账号信息以访问现代化的前端模板。
            </Typography.Text>
          </div>
          {error && <Alert type="error" showIcon message={error} />}
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
              label="密码"
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                size="large"
                prefix={<LockOutlined />}
                placeholder="请输入密码"
                autoComplete="current-password"
              />
            </Form.Item>
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                icon={<LoginOutlined />}
                loading={submitting}
                block
              >
                登录
              </Button>
            </Form.Item>
          </Form>
          <Flex justify="center" gap={8}>
            <Typography.Text type="secondary">还没有账号？</Typography.Text>
            <Link to="/register" className="font-medium text-sky-600">
              立即注册
            </Link>
          </Flex>
        </Space>
      </Card>
    </Flex>
  )
}
