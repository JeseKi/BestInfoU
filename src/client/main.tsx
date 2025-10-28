import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App as AntdApp, ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import 'antd/dist/reset.css'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1668dc',
          borderRadius: 8,
          colorBgLayout: '#f5f7fb',
          fontFamily:
            "'Inter', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', system-ui, -apple-system, sans-serif",
        },
        components: {
          Button: {
            controlHeight: 40,
            fontWeight: 600,
            paddingInline: 16,
          },
          Layout: {
            headerBg: '#ffffff',
            bodyBg: 'transparent',
          },
          Card: {
            borderRadiusLG: 12,
          },
        },
      }}
    >
      <AntdApp>
        <App />
      </AntdApp>
    </ConfigProvider>
  </StrictMode>,
)
