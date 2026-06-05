import { useLocation, useNavigate } from 'react-router-dom';
import {
  Avatar,
  Box,
  Divider,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material';
import AccountBalanceWalletRoundedIcon from '@mui/icons-material/AccountBalanceWalletRounded';
import { navItems } from '@/layouts/navItems';
import { useAuthStore } from '@/store/authStore';

interface Props {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: Props) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const go = (path: string) => {
    navigate(path);
    onNavigate?.();
  };

  return (
    <Stack sx={{ height: '100%' }}>
      <Stack direction="row" alignItems="center" spacing={1.5} sx={{ px: 2.5, py: 2.5 }}>
        <Avatar sx={{ bgcolor: 'primary.main', width: 36, height: 36 }}>
          <AccountBalanceWalletRoundedIcon fontSize="small" />
        </Avatar>
        <Typography variant="h5" fontWeight={800} letterSpacing={-0.5}>
          LedgerIQ
        </Typography>
      </Stack>
      <Divider />

      <List sx={{ px: 1.5, py: 1, flex: 1, overflowY: 'auto' }}>
        {navItems.map((item) => {
          const selected = pathname.startsWith(item.path);
          const Icon = item.icon;
          return (
            <ListItemButton
              key={item.path}
              selected={selected}
              onClick={() => go(item.path)}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                '&.Mui-selected': { bgcolor: 'action.selected' },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40, color: selected ? 'primary.main' : 'inherit' }}>
                <Icon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{
                  fontWeight: selected ? 700 : 500,
                  fontSize: 14,
                }}
              />
            </ListItemButton>
          );
        })}
      </List>

      <Divider />
      <Box sx={{ px: 2.5, py: 2 }}>
        <Typography variant="body2" fontWeight={600} noWrap>
          {user?.full_name ?? 'Account'}
        </Typography>
        <Typography variant="caption" color="text.secondary" noWrap display="block">
          {user?.email ?? ''}
        </Typography>
      </Box>
    </Stack>
  );
}
