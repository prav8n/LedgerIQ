import type { ReactNode } from 'react';
import { Avatar, Box, Card, CardContent, Stack, Typography } from '@mui/material';
import AccountBalanceWalletRoundedIcon from '@mui/icons-material/AccountBalanceWalletRounded';

interface Props {
  title: string;
  subtitle: string;
  children: ReactNode;
}

/** Centered card shell shared by Login and Register. */
export function AuthCard({ title, subtitle, children }: Props) {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        p: 2,
        bgcolor: 'background.default',
        backgroundImage: (t) =>
          `radial-gradient(1200px 600px at 100% -10%, ${t.palette.primary.main}22, transparent),
           radial-gradient(900px 500px at -10% 110%, ${t.palette.secondary.main}1f, transparent)`,
      }}
    >
      <Card sx={{ width: '100%', maxWidth: 420 }} elevation={0}>
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          <Stack spacing={1} alignItems="center" sx={{ mb: 3 }}>
            <Avatar sx={{ bgcolor: 'primary.main', width: 48, height: 48, mb: 1 }}>
              <AccountBalanceWalletRoundedIcon />
            </Avatar>
            <Typography variant="h4" fontWeight={800}>
              {title}
            </Typography>
            <Typography variant="body2" color="text.secondary" textAlign="center">
              {subtitle}
            </Typography>
          </Stack>
          {children}
        </CardContent>
      </Card>
    </Box>
  );
}
