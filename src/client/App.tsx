import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import AdminLayout from './components/layout/AdminLayout'
import ExamplePage from './pages/dashboard/ExamplePage'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import RssManagementPage from './pages/admin/RssManagementPage'
import { AuthProvider /* , RequireAuth */ } from './providers/AuthProvider'

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/"
            element={(
              <>
                {/* 登录暂时关闭，后续若恢复可重新包裹 RequireAuth */}
                <MainLayout />
              </>
            )}
          >
            <Route index element={<ExamplePage />} />
            <Route path="admin" element={<AdminLayout />}>
              <Route index element={<Navigate to="rss" replace />} />
              <Route path="rss" element={<RssManagementPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  )
}
