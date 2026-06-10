import { useState, type FormEvent } from 'react';
import { Box, Button, Card, CardContent, Stack, TextField, Typography } from '@mui/material';

import { PageHeader } from '@/components/PageHeader';
import { useAuthStore } from '@/store/authStore';
import { useToast } from '@/hooks/useToast';
import { authService } from '@/services/authService';
import { getErrorMessage } from '@/services/api';

export function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const toast = useToast();

  // Profile form (name + date of birth)
  const [name, setName] = useState(user?.full_name ?? '');
  const [dob, setDob] = useState(user?.date_of_birth ?? '');
  const [profileBusy, setProfileBusy] = useState(false);

  // Change-email form
  const [newEmail, setNewEmail] = useState('');
  const [emailPw, setEmailPw] = useState('');
  const [emailBusy, setEmailBusy] = useState(false);

  // Change-password form
  const [curPw, setCurPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [pwBusy, setPwBusy] = useState(false);

  const submitProfile = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setProfileBusy(true);
    try {
      const updated = await authService.updateProfile({
        full_name: name.trim() || null,
        date_of_birth: dob || null,
      });
      setUser(updated);
      toast.success('Profile updated');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setProfileBusy(false);
    }
  };

  const submitEmail = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!newEmail.trim() || !emailPw) {
      toast.error('Enter the new email and your current password');
      return;
    }
    setEmailBusy(true);
    try {
      const updated = await authService.changeEmail({
        new_email: newEmail.trim(),
        current_password: emailPw,
      });
      setUser(updated);
      toast.success('Email updated');
      setNewEmail('');
      setEmailPw('');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setEmailBusy(false);
    }
  };

  const submitPassword = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (newPw.length < 8) {
      toast.error('New password must be at least 8 characters');
      return;
    }
    if (newPw !== confirmPw) {
      toast.error('New passwords do not match');
      return;
    }
    setPwBusy(true);
    try {
      await authService.changePassword({ current_password: curPw, new_password: newPw });
      toast.success('Password updated');
      setCurPw('');
      setNewPw('');
      setConfirmPw('');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setPwBusy(false);
    }
  };

  return (
    <Box>
      <PageHeader title="Settings" subtitle="Manage your account" />

      <Stack spacing={3} maxWidth={560}>
        <Card>
          <CardContent>
            <Typography variant="overline" color="text.secondary">
              Signed in as
            </Typography>
            <Typography variant="h6">{user?.email ?? '—'}</Typography>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Box component="form" onSubmit={submitProfile}>
              <Typography variant="h6" mb={2}>
                Profile
              </Typography>
              <Stack spacing={2}>
                <TextField
                  label="Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  fullWidth
                />
                <TextField
                  label="Date of birth"
                  type="date"
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                />
                <Box>
                  <Button type="submit" variant="contained" disabled={profileBusy}>
                    {profileBusy ? 'Saving…' : 'Save profile'}
                  </Button>
                </Box>
              </Stack>
            </Box>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Box component="form" onSubmit={submitEmail}>
              <Typography variant="h6" mb={2}>
                Change email
              </Typography>
              <Stack spacing={2}>
                <TextField
                  label="New email"
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  fullWidth
                  required
                />
                <TextField
                  label="Current password"
                  type="password"
                  value={emailPw}
                  onChange={(e) => setEmailPw(e.target.value)}
                  fullWidth
                  required
                />
                <Box>
                  <Button type="submit" variant="contained" disabled={emailBusy}>
                    {emailBusy ? 'Saving…' : 'Update email'}
                  </Button>
                </Box>
              </Stack>
            </Box>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Box component="form" onSubmit={submitPassword}>
              <Typography variant="h6" mb={2}>
                Change password
              </Typography>
              <Stack spacing={2}>
                <TextField
                  label="Current password"
                  type="password"
                  value={curPw}
                  onChange={(e) => setCurPw(e.target.value)}
                  fullWidth
                  required
                />
                <TextField
                  label="New password"
                  type="password"
                  value={newPw}
                  onChange={(e) => setNewPw(e.target.value)}
                  fullWidth
                  required
                  helperText="At least 8 characters"
                />
                <TextField
                  label="Confirm new password"
                  type="password"
                  value={confirmPw}
                  onChange={(e) => setConfirmPw(e.target.value)}
                  fullWidth
                  required
                />
                <Box>
                  <Button type="submit" variant="contained" disabled={pwBusy}>
                    {pwBusy ? 'Saving…' : 'Update password'}
                  </Button>
                </Box>
              </Stack>
            </Box>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
