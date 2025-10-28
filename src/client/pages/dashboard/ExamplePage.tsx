import { isAxiosError } from 'axios'
import {
  Alert,
  App,
  Avatar,
  Button,
  Card,
  Empty,
  Flex,
  List,
  Select,
  Space,
  Spin,
  Tag,
  Typography,
} from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import { useCallback, useEffect, useMemo, useState } from 'react'
import * as rssApi from '../../lib/rss'
import type { RSSEntry, RSSSource } from '../../lib/types'

type SourceFilterValue = number | 'all'

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

function formatDateTime(value: string | null): string {
  if (!value) {
    return '发布时间未知'
  }
  try {
    return new Date(value).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch (error) {
    console.error('时间格式化失败', error)
    return value
  }
}

export default function FeedPage() {
  const { message } = App.useApp()

  const [loading, setLoading] = useState(false)
  const [refreshLoading, setRefreshLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [sources, setSources] = useState<RSSSource[]>([])
  const [entries, setEntries] = useState<RSSEntry[]>([])
  const [selectedSourceId, setSelectedSourceId] = useState<SourceFilterValue>('all')

  const loadFeed = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await rssApi.fetchFeedSnapshot(50)
      const nextSources = Array.isArray(data.sources) ? data.sources : []
      const nextEntries = Array.isArray(data.entries) ? data.entries : []
      setSources(nextSources)
      setEntries(nextEntries)
      setSelectedSourceId((prev) => {
        if (nextSources.length === 0) {
          return 'all'
        }
        if (prev === 'all') {
          return nextSources[0].id
        }
        const exists = nextSources.some((source) => source.id === prev)
        return exists ? prev : nextSources[0].id
      })
    } catch (err) {
      const text = resolveErrorMessage(err)
      setError(text)
      message.error(text)
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    void loadFeed()
  }, [loadFeed])

  const handleRefresh = async () => {
    if (selectedSourceId === 'all') {
      message.info('请选择具体的订阅源后再刷新。')
      return
    }
    setRefreshLoading(true)
    try {
      await rssApi.refreshSource(selectedSourceId)
      message.success('刷新成功，正在更新列表')
      await loadFeed()
    } catch (err) {
      const text = resolveErrorMessage(err)
      message.error(text)
    } finally {
      setRefreshLoading(false)
    }
  }

  const visibleEntries = useMemo(() => {
    if (selectedSourceId === 'all') {
      return entries
    }
    return entries.filter((entry) => entry.source_id === selectedSourceId)
  }, [entries, selectedSourceId])

  const activeSource = useMemo(() => {
    if (selectedSourceId === 'all') {
      return null
    }
    return sources.find((source) => source.id === selectedSourceId) ?? null
  }, [selectedSourceId, sources])

  const filterOptions = useMemo(() => {
    const base = sources.map((source) => ({
      label: source.name,
      value: source.id,
    }))
    return [{ label: '全部来源', value: 'all' as const }, ...base]
  }, [sources])

  return (
    <Flex vertical gap={24}>
      <Card
        title="订阅源管理"
        extra={
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            loading={refreshLoading}
            onClick={handleRefresh}
            disabled={sources.length === 0}
          >
            刷新当前来源
          </Button>
        }
      >
        <Flex vertical gap={16}>
          <Typography.Paragraph type="secondary">
            选择订阅源后可以手动刷新，系统默认会按抓取频率自动同步。
          </Typography.Paragraph>
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <Select<SourceFilterValue>
              style={{ width: 240 }}
              options={filterOptions}
              value={selectedSourceId}
              onChange={(value) => setSelectedSourceId(value)}
              placeholder="请选择订阅源"
            />
            {activeSource ? (
              <Card type="inner" title={activeSource.name}>
                <Space direction="vertical" size={8}>
                  <Typography.Text>
                    链接：<a href={activeSource.feed_url} target="_blank" rel="noreferrer">{activeSource.feed_url}</a>
                  </Typography.Text>
                  {activeSource.description && (
                    <Typography.Paragraph>
                      {activeSource.description}
                    </Typography.Paragraph>
                  )}
                  <Space size={8} wrap>
                    {activeSource.category && <Tag color="blue">{activeSource.category}</Tag>}
                    {activeSource.language && <Tag color="green">{activeSource.language}</Tag>}
                    {activeSource.is_active ? <Tag color="cyan">已启用</Tag> : <Tag color="default">已停用</Tag>}
                  </Space>
                </Space>
              </Card>
            ) : (
              <Alert message="当前展示全部来源的合集。" type="info" showIcon />
            )}
          </Space>
        </Flex>
      </Card>

      <Card title="最新内容">
        {error && <Alert type="error" showIcon message={error} className="mb-4" />}
        <Spin spinning={loading} tip="正在加载订阅内容...">
          {visibleEntries.length === 0 ? (
            <Empty description="暂无可展示的条目" />
          ) : (
            <List
              itemLayout="vertical"
              dataSource={visibleEntries}
              renderItem={(item) => (
                <List.Item key={item.id}
                  extra={item.feed_avatar ? <Avatar shape="square" size={64} src={item.feed_avatar} /> : undefined}
                >
                  <Space direction="vertical" size={8} style={{ width: '100%' }}>
                    <Space align="center" size={12}>
                      <Tag color="blue">{item.source_name}</Tag>
                      <Typography.Text type="secondary">{formatDateTime(item.published_at)}</Typography.Text>
                    </Space>
                    <Typography.Title level={4} style={{ margin: 0 }}>
                      {item.link ? (
                        <a href={item.link} target="_blank" rel="noreferrer">
                          {item.title}
                        </a>
                      ) : (
                        item.title
                      )}
                    </Typography.Title>
                    {item.author && (
                      <Typography.Text type="secondary">作者：{item.author}</Typography.Text>
                    )}
                    {item.summary && (
                      <Typography.Paragraph>
                        <span dangerouslySetInnerHTML={{ __html: item.summary }} />
                      </Typography.Paragraph>
                    )}
                  </Space>
                </List.Item>
              )}
            />
          )}
        </Spin>
      </Card>
    </Flex>
  )
}
