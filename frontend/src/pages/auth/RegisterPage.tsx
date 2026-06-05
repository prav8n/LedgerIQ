import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link as RouterLink, Navigate, useNavigate } from 'react-router-dom';
import { Button, Link, Stack, TextField, Typography } from '@mui/material';
import { AuthCard } from '@/pages/auth/AuthCard';
import { authService } from '@/services/authService';
import { getErrorMessage } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { useToast } from '@/hooks/useToast';
import { paths } from '@/routes/paths';

interface RegisterFormValues {
  full_name: string;
  email: string;
  password: string;
}

export function RegisterPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const setAuth = useAuthStore((s) => s.setAuth);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    defaultValues: { full_name: '', email: '', password: '' },
  });

  if (isAuthenticated) {
    return <Navigate to={paths.dashboard} replace />;
  }

  const onSubmit = async (values: RegisterFormValues) => {
    setSubmitting(true);
    try {
      const res = await authService.register({
        email: values.email,
        password: values.password,
        full_name: values.full_name || undefined,
      });
      setAuth(res.user, res.tokens);
      toast.success('Account created');
      navigate(paths.dashboard, { replace: true });
    } catch (error) {
      toast.error(getErrorMessage(error, 'Registration failed'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthCard title="Create account" subtitle="Start managing your money with LedgerIQ">
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <Stack spacing={2.5}>
          <TextField
            label="Full name"
            autoComplete="name"
            fullWidth
            error={Boolean(errors.full_name)}
            helperText={errors.full_name?.message}
            {...register('full_name', {
              maxLength: { value: 120, message: 'Name is too long' },
            })}
          />
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
            autoComplete="new-password"
            fullWidth
            error={Boolean(errors.password)}
            helperText={errors.password?.message ?? 'At least 8 characters'}
            {...register('password', {
              required: 'Password is required',
              minLength: { value: 8, message: 'Password must be at least 8 characters' },
              maxLength: { value: 72, message: 'Password is too long' },
            })}
          />
          <Button type="submit" variant="contained" size="large" disabled={submitting}>
            {submitting ? 'Creating account…' : 'Create account'}
          </Button>
          <Typography variant="body2" textAlign="center" color="text.secondary">
            Already have an account?{' '}
            <Link component={RouterLink} to={paths.login} fontWeight={600}>
              Sign in
            </Link>
          </Typography>
        </Stack>
      </form>
    </AuthCard>
  );
}
