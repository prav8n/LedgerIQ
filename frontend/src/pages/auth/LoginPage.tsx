import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Button, Stack, TextField } from '@mui/material';
import { AuthCard } from '@/pages/auth/AuthCard';
import { authService } from '@/services/authService';
import { getErrorMessage } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { useToast } from '@/hooks/useToast';
import { paths } from '@/routes/paths';
import type { LoginRequest } from '@/types/auth';

interface LocationState {
  from?: { pathname?: string };
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const setAuth = useAuthStore((s) => s.setAuth);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginRequest>({ defaultValues: { email: '', password: '' } });

  if (isAuthenticated) {
    return <Navigate to={paths.dashboard} replace />;
  }

  const onSubmit = async (values: LoginRequest) => {
    setSubmitting(true);
    try {
      const res = await authService.login(values);
      setAuth(res.user, res.tokens);
      toast.success(`Welcome back, ${res.user.full_name ?? res.user.email}`);
      const dest = (location.state as LocationState | null)?.from?.pathname ?? paths.dashboard;
      navigate(dest, { replace: true });
    } catch (error) {
      toast.error(getErrorMessage(error, 'Login failed'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthCard title="LedgerIQ" subtitle="Sign in to your account">
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <Stack spacing={2.5}>
          <TextField
            label="Email"
            type="email"
            autoComplete="email"
            fullWidth
            error={Boolean(errors.email)}
            helperText={errors.email?.message}
            {...register('email', {
              required: 'Email is required',
              pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Enter a valid email' },
            })}
          />
          <TextField
            label="Password"
            type="password"
            autoComplete="current-password"
            fullWidth
            error={Boolean(errors.password)}
            helperText={errors.password?.message}
            {...register('password', { required: 'Password is required' })}
          />
          <Button type="submit" variant="contained" size="large" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </Button>
        </Stack>
      </form>
    </AuthCard>
  );
}
