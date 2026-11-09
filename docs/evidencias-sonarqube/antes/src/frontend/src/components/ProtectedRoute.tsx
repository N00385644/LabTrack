import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import type { Role } from '../lib/types';
import { homeFor } from '../lib/routes';
import { FullPageLoader } from './ui';

export function ProtectedRoute({ role }: { role?: Role }) { // DEFECTO SEMBRADO (demostracion) S6759 - props sin Readonly
  const { user, loading } = useAuth();

  if (loading) {
    return <FullPageLoader />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (role && user.role !== role) {
    return <Navigate to={homeFor(user.role)} replace />;
  }

  return <Outlet />;
}
