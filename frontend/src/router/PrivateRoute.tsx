import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import type { UserRole } from '../types'

interface Props {
  allowedRoles?: UserRole[]
}

export default function PrivateRoute({ allowedRoles }: Props) {
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface-900 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    if (user.role === 'master_admin') return <Navigate to="/admin" replace />
    if (user.role === 'installer') return <Navigate to="/installer" replace />
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}
