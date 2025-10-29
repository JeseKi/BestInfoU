import { useMemo } from 'react'
import { Layout, Menu, theme } from 'antd'
import type { MenuProps } from 'antd'
import { Link, Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

const { Sider, Content } = Layout

export default function AdminLayout() {
  const location = useLocation()
  const { user } = useAuth()
  const { token } = theme.useToken()

  const selectedKeys = useMemo(() => {
    if (location.pathname.startsWith('/admin/rss')) {
      return ['admin-rss']
    }
    return []
  }, [location.pathname])

  const menuItems = useMemo<MenuProps['items']>(
    () => [
      {
        key: 'admin-rss',
        label: <Link to="/admin/rss">RSS 管理</Link>,
      },
    ],
    [],
  )

  if (!user || user.role !== 'admin') {
    return <Navigate to="/" replace />
  }

  return (
    <Layout
      style={{
        minHeight: '60vh',
        background: 'transparent',
      }}
    >
      <Sider
        width={220}
        style={{
          background: token.colorBgElevated,
          borderRadius: 12,
          paddingBlock: 24,
          paddingInline: 16,
          marginRight: 24,
        }}
      >
        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          items={menuItems}
          style={{
            borderInline: 'none',
            background: 'transparent',
          }}
        />
      </Sider>
      <Content style={{ flex: 1 }}>
        <Outlet />
      </Content>
    </Layout>
  )
}
