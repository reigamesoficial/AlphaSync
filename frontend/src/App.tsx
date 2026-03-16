import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from './context/AuthContext'
import PrivateRoute from './router/PrivateRoute'
import AppLayout from './components/layout/AppLayout'
import AdminLayout from './components/layout/AdminLayout'
import InstallerLayout from './components/layout/InstallerLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Clients from './pages/Clients'
import Conversations from './pages/Conversations'
import Quotes from './pages/Quotes'
import Settings from './pages/Settings'
import Measures from './pages/Measures'
import Schedule from './pages/Schedule'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminCompanies from './pages/admin/AdminCompanies'
import AdminUsers from './pages/admin/AdminUsers'
import AdminMetrics from './pages/admin/AdminMetrics'
import AdminSettings from './pages/admin/AdminSettings'
import InstallerSchedule from './pages/installer/InstallerSchedule'

function RootRedirect() {
  const { isAuthenticated, isLoading, user } = useAuth()
  if (isLoading) return null
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (user?.role === 'master_admin') return <Navigate to="/admin" replace />
  if (user?.role === 'installer') return <Navigate to="/installer" replace />
  return <Navigate to="/dashboard" replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Painel Master (MASTER_ADMIN) */}
          <Route element={<PrivateRoute allowedRoles={['master_admin']} />}>
            <Route element={<AdminLayout />}>
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/admin/companies" element={<AdminCompanies />} />
              <Route path="/admin/users" element={<AdminUsers />} />
              <Route path="/admin/metrics" element={<AdminMetrics />} />
              <Route path="/admin/settings" element={<AdminSettings />} />
            </Route>
          </Route>

          {/* Painel Instalador (INSTALLER) */}
          <Route element={<PrivateRoute allowedRoles={['installer']} />}>
            <Route element={<InstallerLayout />}>
              <Route path="/installer" element={<InstallerSchedule />} />
            </Route>
          </Route>

          {/* Painel Operacional (COMPANY_ADMIN + SELLER) */}
          <Route element={<PrivateRoute allowedRoles={['company_admin', 'seller']} />}>
            <Route element={<AppLayout />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/clients" element={<Clients />} />
              <Route path="/conversations" element={<Conversations />} />
              <Route path="/quotes" element={<Quotes />} />
              <Route path="/measures" element={<Measures />} />
              <Route path="/schedule" element={<Schedule />} />
              {/* Configurações: apenas company_admin */}
              <Route element={<PrivateRoute allowedRoles={['company_admin']} />}>
                <Route path="/settings" element={<Settings />} />
              </Route>
            </Route>
          </Route>

          <Route path="/" element={<RootRedirect />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
