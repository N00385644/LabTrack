import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/AppLayout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { FullPageLoader } from './components/ui';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import { homeFor } from './lib/routes';
import AdminHistoryPage from './pages/AdminHistoryPage';
import AdminPendingPage from './pages/AdminPendingPage';
import AdminReturnsPage from './pages/AdminReturnsPage';
import CatalogPage from './pages/CatalogPage';
import LoginPage from './pages/LoginPage';
import MyReservationsPage from './pages/MyReservationsPage';
import NewReservationPage from './pages/NewReservationPage';
import NotFoundPage from './pages/NotFoundPage';

function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <FullPageLoader />;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={homeFor(user.role)} replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/" element={<HomeRedirect />} />
            <Route path="/login" element={<LoginPage />} />

            <Route element={<ProtectedRoute role="STUDENT" />}>
              <Route element={<AppLayout />}>
                <Route path="/catalogo" element={<CatalogPage />} />
                <Route path="/reservar" element={<NewReservationPage />} />
                <Route path="/mis-reservas" element={<MyReservationsPage />} />
              </Route>
            </Route>

            <Route element={<ProtectedRoute role="ADMIN" />}>
              <Route element={<AppLayout />}>
                <Route path="/admin/pendientes" element={<AdminPendingPage />} />
                <Route path="/admin/devoluciones" element={<AdminReturnsPage />} />
                <Route path="/admin/historial" element={<AdminHistoryPage />} />
              </Route>
            </Route>

            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
