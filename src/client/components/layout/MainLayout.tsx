import { useMemo } from 'react'
import {
  Avatar,
  Dropdown,
  Flex,
  Layout,
  Menu,
  type MenuProps,
  Typography,
  theme,
} from 'antd'
import {
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

const { Header, Content } = Layout

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { token } = theme.useToken()
  const { user, logout } = useAuth()

  const selectedKeys = useMemo(() => {
    if (location.pathname.startsWith('/')) {
      return ['dashboard']
    }
    return []
  }, [location.pathname])

  const navItems = useMemo<MenuProps['items']>(
    () => [
      {
        key: 'dashboard',
        label: <Link to="/">示例模块</Link>,
      },
    ],
    [],
  )

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const userMenu = useMemo<MenuProps['items']>(
    () => [
      {
        key: 'profile',
        label: (
          <Flex vertical gap={2} style={{ minWidth: 180 }}>
            <Typography.Text type="secondary">当前用户</Typography.Text>
            <Typography.Text strong>{user?.username ?? '未登录'}</Typography.Text>
          </Flex>
        ),
        disabled: true,
      },
      { type: 'divider' },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
      },
    ],
    [user?.username],
  )

  const handleUserMenuClick: MenuProps['onClick'] = ({ key }) => {
    if (key === 'logout') {
      handleLogout()
    }
  }

  return (
    <Layout style={{ minHeight: '100vh', background: token.colorBgLayout }}>
      <Header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingInline: 24,
          paddingBlock: 12,
          background: token.colorBgElevated,
          boxShadow: '0 2px 12px rgba(15, 23, 42, 0.06)',
        }}
      >
        <Flex align="center" gap={16}>
          <Link to="/" className="text-base font-semibold text-slate-900">
            Fullstack Template
          </Link>
          <Menu
            mode="horizontal"
            selectedKeys={selectedKeys}
            items={navItems}
            style={{ borderBottom: 'none', background: 'transparent' }}
          />
        </Flex>
        <Dropdown
          menu={{ items: userMenu, onClick: handleUserMenuClick }}
          placement="bottomRight"
          arrow
          trigger={["hover"]}
          getPopupContainer={() => document.body}
          overlayStyle={{ zIndex: 1000 }}
        >
          <Avatar
            size="large"
            icon={<UserOutlined />}
            style={{ background: token.colorPrimary, cursor: 'pointer' }}
          />
        </Dropdown>
      </Header>
      <Content style={{ padding: '32px 24px 48px' }}>
        <div
          style={{
            margin: '0 auto',
            maxWidth: 1120,
            width: '100%',
          }}
        >
          <Outlet />
        </div>
      </Content>
    </Layout>
  )
}
