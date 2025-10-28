import { isAxiosError } from 'axios'
import {
  Alert,
  App,
  Button,
  Card,
  Descriptions,
  Flex,
  Form,
  Input,
  InputNumber,
  Result,
  Space,
  Statistic,
  Typography,
} from 'antd'
import {
  ThunderboltOutlined,
  PlusCircleOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { useMemo, useState } from 'react'
import * as exampleApi from '../../lib/example'
import type { Item } from '../../lib/types'

function resolveErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const payload = error.response?.data as { detail?: string; message?: string } | undefined
    return payload?.detail ?? payload?.message ?? '请求失败，请稍后再试。'
  }
  if (error instanceof Error) {
    return error.message
  }
  return '请求失败，请稍后再试。'
}

export default function ExamplePage() {
  const { message } = App.useApp()

  const [pingLoading, setPingLoading] = useState(false)
  const [pingError, setPingError] = useState<string | null>(null)
  const [pingResult, setPingResult] = useState<string | null>(null)

  const [createForm] = Form.useForm<{ name: string }>()
  const [createLoading, setCreateLoading] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [createdItem, setCreatedItem] = useState<Item | null>(null)

  const [fetchForm] = Form.useForm<{ id: number }>()
  const [fetchLoading, setFetchLoading] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [fetchedItem, setFetchedItem] = useState<Item | null>(null)

  const handlePing = async () => {
    setPingLoading(true)
    setPingError(null)
    try {
      const result = await exampleApi.ping()
      setPingResult(result)
      message.success('服务正常响应')
    } catch (error) {
      const text = resolveErrorMessage(error)
      setPingError(text)
      setPingResult(null)
      message.error(text)
    } finally {
      setPingLoading(false)
    }
  }

  const handleCreateItem = async ({ name }: { name: string }) => {
    const trimmed = name.trim()
    if (!trimmed) {
      setCreateError('名称不能为空')
      return
    }
    setCreateLoading(true)
    setCreateError(null)
    try {
      const item = await exampleApi.createItem({ name: trimmed })
      setCreatedItem(item)
      message.success('示例条目创建成功')
      createForm.resetFields()
    } catch (error) {
      const text = resolveErrorMessage(error)
      setCreateError(text)
      setCreatedItem(null)
      message.error(text)
    } finally {
      setCreateLoading(false)
    }
  }

  const handleFetchItem = async ({ id }: { id: number }) => {
    setFetchLoading(true)
    setFetchError(null)
    try {
      const item = await exampleApi.getItem(id)
      setFetchedItem(item)
      message.success('查询成功')
    } catch (error) {
      const text = resolveErrorMessage(error)
      setFetchError(text)
      setFetchedItem(null)
      message.error(text)
    } finally {
      setFetchLoading(false)
    }
  }

  const statisticValue = useMemo(() => {
    if (pingResult) {
      return '可用'
    }
    if (pingError) {
      return '异常'
    }
    return '待检测'
  }, [pingError, pingResult])

  return (
    <Flex vertical gap={24}>
      <Card
        title="服务健康监控"
        extra={
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            loading={pingLoading}
            onClick={handlePing}
          >
            {pingLoading ? '检测中' : '发起检测'}
          </Button>
        }
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Typography.Paragraph type="secondary">
            这里会调用后端的 ping 接口，确认服务是否正常运行，并同步展示最新状态。
          </Typography.Paragraph>
          <Statistic
            title="当前服务状态"
            value={statisticValue}
            valueStyle={{ color: statisticValue === '异常' ? '#dc2626' : '#1668dc' }}
          />
          {pingError && <Alert type="error" showIcon message={pingError} />}
          {!pingError && pingResult && (
            <Result
              status="success"
              title={pingResult}
              subTitle="后端服务已成功响应请求。"
            />
          )}
          {!pingError && !pingResult && (
            <Alert type="info" showIcon message="尚未发起检测，请点击上方按钮。" />
          )}
        </Space>
      </Card>

      <Card title="创建示例条目">
        <Typography.Paragraph type="secondary">
          填写名称后提交，将调用后端创建接口并返回新条目的详细信息。
        </Typography.Paragraph>
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreateItem}
          requiredMark={false}
          className="mt-6"
        >
          <Form.Item
            label="条目名称"
            name="name"
            rules={[
              { required: true, message: '请输入条目名称' },
              { min: 2, message: '名称至少需要 2 个字符' },
            ]}
          >
            <Input size="large" placeholder="例如：现代化前端" allowClear />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={createLoading}
              icon={<PlusCircleOutlined />}
            >
              创建条目
            </Button>
          </Form.Item>
        </Form>
        {createError && <Alert type="error" showIcon message={createError} className="mt-4" />}
        {createdItem && (
          <Result
            status="success"
            title="创建成功"
            extra={
              <Descriptions column={1} bordered size="small">
                <Descriptions.Item label="条目 ID">{createdItem.id}</Descriptions.Item>
                <Descriptions.Item label="条目名称">{createdItem.name}</Descriptions.Item>
              </Descriptions>
            }
          />
        )}
      </Card>

      <Card title="查询示例条目">
        <Typography.Paragraph type="secondary">
          输入条目 ID 并提交，将带回后端的查询结果，便于快速验证数据。
        </Typography.Paragraph>
        <Form
          form={fetchForm}
          layout="vertical"
          onFinish={handleFetchItem}
          requiredMark={false}
          className="mt-6"
        >
          <Form.Item
            label="条目 ID"
            name="id"
            rules={[
              { required: true, message: '请输入条目 ID' },
              {
                type: 'number',
                min: 1,
                transform: (value) => (value ?? undefined),
                message: '请输入大于 0 的整数',
              },
            ]}
          >
            <InputNumber
              min={1}
              size="large"
              style={{ width: '100%' }}
              placeholder="请输入条目 ID"
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={fetchLoading}
              icon={<SearchOutlined />}
            >
              查询条目
            </Button>
          </Form.Item>
        </Form>
        {fetchError && <Alert type="error" showIcon message={fetchError} className="mt-4" />}
        {fetchedItem && (
          <Card
            type="inner"
            title="查询结果"
            className="mt-4"
          >
            <Descriptions column={1} size="small" labelStyle={{ width: 96 }}>
              <Descriptions.Item label="条目 ID">{fetchedItem.id}</Descriptions.Item>
              <Descriptions.Item label="条目名称">{fetchedItem.name}</Descriptions.Item>
            </Descriptions>
          </Card>
        )}
      </Card>
    </Flex>
  )
}
