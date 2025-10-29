import { isAxiosError } from 'axios'
import {
  App,
  Button,
  Card,
  Flex,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  RetweetOutlined,
} from '@ant-design/icons'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type {
  CreateSourcePayload,
  RSSSource,
  UpdateSourcePayload,
} from '../../lib/types'
import * as rssApi from '../../lib/rss'

type SourceFormValues = {
  name: string
  feed_url: string
  homepage_url?: string | null
  feed_avatar?: string | null
  description?: string | null
  language?: string | null
  category?: string | null
  is_active: boolean
}

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

function normalizePayload(values: SourceFormValues): CreateSourcePayload {
  return {
    name: values.name.trim(),
    feed_url: values.feed_url.trim(),
    homepage_url: values.homepage_url?.trim() || undefined,
    feed_avatar: values.feed_avatar?.trim() || undefined,
    description: values.description?.trim() || undefined,
    language: values.language?.trim() || undefined,
    category: values.category?.trim() || undefined,
    is_active: values.is_active,
  }
}

export default function RssManagementPage() {
  const { message } = App.useApp()
  const [sources, setSources] = useState<RSSSource[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalSubmitting, setModalSubmitting] = useState(false)
  const [editingSource, setEditingSource] = useState<RSSSource | null>(null)
  const [refreshingId, setRefreshingId] = useState<number | null>(null)
  const [toggleLoadingId, setToggleLoadingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [form] = Form.useForm<SourceFormValues>()

  const loadSources = useCallback(async () => {
    setLoading(true)
    try {
      const data = await rssApi.fetchSources()
      setSources(data)
    } catch (error) {
      const text = resolveErrorMessage(error)
      message.error(text)
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    void loadSources()
  }, [loadSources])

  const handleOpenCreate = useCallback(() => {
    setEditingSource(null)
    setModalVisible(true)
    form.setFieldsValue({
      name: '',
      feed_url: '',
      homepage_url: '',
      feed_avatar: '',
      description: '',
      language: '',
      category: '',
      is_active: true,
    })
  }, [form])

  const handleOpenEdit = useCallback((source: RSSSource) => {
    setEditingSource(source)
    setModalVisible(true)
    form.setFieldsValue({
      name: source.name,
      feed_url: source.feed_url,
      homepage_url: source.homepage_url ?? '',
      feed_avatar: source.feed_avatar ?? '',
      description: source.description ?? '',
      language: source.language ?? '',
      category: source.category ?? '',
      is_active: source.is_active,
    })
  }, [form])

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const payload = normalizePayload(values)
      setModalSubmitting(true)

      if (editingSource) {
        const data = await rssApi.updateSource(editingSource.id, payload as UpdateSourcePayload)
        setSources((prev) =>
          prev.map((item) => (item.id === data.id ? data : item)),
        )
        message.success('订阅源已更新')
      } else {
        const data = await rssApi.createSource(payload)
        setSources((prev) => [data, ...prev])
        message.success('订阅源已创建')
      }
      setModalVisible(false)
      setEditingSource(null)
      form.resetFields()
    } catch (error) {
      if (error instanceof Error && 'errorFields' in error) {
        return
      }
      const text = resolveErrorMessage(error)
      message.error(text)
    } finally {
      setModalSubmitting(false)
    }
  }

  const handleRefreshSource = useCallback(async (source: RSSSource) => {
    setRefreshingId(source.id)
    try {
      const result = await rssApi.refreshSource(source.id)
      setSources((prev) =>
        prev.map((item) => (item.id === result.source.id ? result.source : item)),
      )
      message.success('刷新成功，已更新最近同步时间')
    } catch (error) {
      message.error(resolveErrorMessage(error))
    } finally {
      setRefreshingId(null)
    }
  }, [message])

  const handleToggleActive = useCallback(async (source: RSSSource, nextValue: boolean) => {
    setToggleLoadingId(source.id)
    try {
      const data = await rssApi.updateSource(
        source.id,
        { is_active: nextValue } as UpdateSourcePayload,
      )
      setSources((prev) =>
        prev.map((item) => (item.id === data.id ? data : item)),
      )
      message.success(nextValue ? '订阅源已启用' : '订阅源已停用')
    } catch (error) {
      message.error(resolveErrorMessage(error))
    } finally {
      setToggleLoadingId(null)
    }
  }, [message])

  const handleDeleteSource = useCallback(async (source: RSSSource) => {
    setDeletingId(source.id)
    try {
      await rssApi.deleteSource(source.id)
      setSources((prev) => prev.filter((item) => item.id !== source.id))
      message.success('订阅源已删除')
    } catch (error) {
      message.error(resolveErrorMessage(error))
    } finally {
      setDeletingId(null)
    }
  }, [message])

  const columns = useMemo<ColumnsType<RSSSource>>(
    () => [
      {
        title: '名称',
        dataIndex: 'name',
        key: 'name',
        render: (value: string, record) => (
          <Flex vertical gap={4}>
            <Typography.Text strong>{value}</Typography.Text>
            {record.category && <Tag color="blue">{record.category}</Tag>}
          </Flex>
        ),
      },
      {
        title: '订阅链接',
        dataIndex: 'feed_url',
        key: 'feed_url',
        render: (value: string) => (
          <Typography.Link href={value} target="_blank" rel="noreferrer">
            {value}
          </Typography.Link>
        ),
      },
      {
        title: '头像',
        dataIndex: 'feed_avatar',
        key: 'feed_avatar',
        render: (value: string | null) =>
          value ? (
            <Space size={8}>
              <span>
                <img
                  src={value}
                  alt="avatar"
                  style={{ width: 32, height: 32, borderRadius: 6, objectFit: 'cover' }}
                />
              </span>
              <Typography.Link href={value} target="_blank" rel="noreferrer">
                查看
              </Typography.Link>
            </Space>
          ) : (
            <Typography.Text type="secondary">未设置</Typography.Text>
          ),
      },
      {
        title: '最近同步时间',
        dataIndex: 'last_synced_at',
        key: 'last_synced_at',
        render: (value: string | null) =>
          value
            ? new Date(value).toLocaleString('zh-CN', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
            })
            : '尚未同步',
      },
      {
        title: '启用状态',
        dataIndex: 'is_active',
        key: 'is_active',
        render: (_: boolean, record) => (
          <Space size={12}>
            <Switch
              checked={record.is_active}
              loading={toggleLoadingId === record.id}
              onChange={(checked) => handleToggleActive(record, checked)}
            />
            <Tag color={record.is_active ? 'green' : 'default'}>
              {record.is_active ? '已启用' : '已停用'}
            </Tag>
          </Space>
        ),
      },
      {
        title: '操作',
        key: 'actions',
        render: (_: unknown, record) => (
          <Space size={12}>
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleOpenEdit(record)}
            >
              编辑
            </Button>
            <Button
              type="link"
              icon={<ReloadOutlined />}
              loading={refreshingId === record.id}
              onClick={() => handleRefreshSource(record)}
            >
              刷新
            </Button>
            <Popconfirm
              title="删除订阅源"
              description="删除后将同时移除历史条目，确认继续？"
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true, loading: deletingId === record.id }}
              onConfirm={() => handleDeleteSource(record)}
              disabled={deletingId === record.id}
            >
              <Button
                type="link"
                danger
                icon={<DeleteOutlined />}
                loading={deletingId === record.id}
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [deletingId, handleRefreshSource, handleOpenEdit, handleToggleActive, refreshingId, toggleLoadingId, handleDeleteSource],
  )

  return (
    <Flex vertical gap={24}>
      <Card
        title="RSS 管理"
        extra={(
          <Space size={12}>
            <Button
              icon={<RetweetOutlined />}
              onClick={() => loadSources()}
              loading={loading}
            >
              重新加载
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleOpenCreate}
            >
              新增订阅源
            </Button>
          </Space>
        )}
      >
        <Typography.Paragraph type="secondary">
          管理 RSS 订阅源，支持新增、编辑、启用/停用、刷新抓取以及删除。刷新操作会触发抓取器立即运行。
        </Typography.Paragraph>
        <Table<RSSSource>
          rowKey="id"
          dataSource={sources}
          loading={loading}
          columns={columns}
          pagination={false}
        />
      </Card>

      <Modal
        open={modalVisible}
        title={editingSource ? '编辑订阅源' : '新增订阅源'}
        okText="保存"
        cancelText="取消"
        confirmLoading={modalSubmitting}
        onCancel={() => {
          setModalVisible(false)
          setEditingSource(null)
          form.resetFields()
        }}
        onOk={handleSubmit}
        destroyOnClose
      >
        <Form<SourceFormValues>
          form={form}
          layout="vertical"
          initialValues={{
            is_active: true,
          }}
        >
          <Form.Item
            label="名称"
            name="name"
            rules={[{ required: true, message: '请输入订阅源名称' }]}
          >
            <Input placeholder="请输入订阅源名称" />
          </Form.Item>
          <Form.Item
            label="订阅链接"
            name="feed_url"
            rules={[
              { required: true, message: '请输入订阅链接' },
              { type: 'url', message: '请输入合法的 URL 地址' },
            ]}
          >
            <Input placeholder="https://example.com/feed.xml" />
          </Form.Item>
          <Form.Item
            label="主页地址"
            name="homepage_url"
            rules={[{ type: 'url', message: '请输入合法的 URL 地址' }]}
          >
            <Input placeholder="https://example.com" />
          </Form.Item>
          <Form.Item label="简介" name="description">
            <Input.TextArea
              placeholder="简单介绍订阅源内容，便于团队成员识别"
              rows={3}
              maxLength={1024}
              showCount
            />
          </Form.Item>
          <Form.Item label="分类" name="category">
            <Input placeholder="例如 technology、product、design" />
          </Form.Item>
          <Form.Item
            label="头像地址"
            name="feed_avatar"
            rules={[{ type: 'url', message: '请输入合法的 URL 地址' }]}
          >
            <Input placeholder="https://example.com/avatar.png" />
          </Form.Item>
          <Form.Item label="语言" name="language">
            <Input placeholder="例如 zh-CN、en-US" />
          </Form.Item>
          <Form.Item
            label="是否启用"
            name="is_active"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </Flex>
  )
}
