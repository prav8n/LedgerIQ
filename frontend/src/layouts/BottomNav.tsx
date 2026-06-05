import { useLocation, useNavigate } from 'react-router-dom';
import { BottomNavigation, BottomNavigationAction, Paper } from '@mui/material';
import { bottomNavItems } from '@/layouts/navItems';

export function BottomNav() {
  const { pathname } = useLocation();
  const navigate = useNavigate();

  const current =
    bottomNavItems.find((item) => pathname.startsWith(item.path))?.path ?? false;

  return (
    <Paper
      elevation={0}
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: (t) => t.zIndex.appBar,
        borderTop: (t) => `1px solid ${t.palette.divider}`,
      }}
    >
      <BottomNavigation
        showLabels
        value={current}
        onChange={(_, value: string) => navigate(value)}
      >
        {bottomNavItems.map((item) => {
          const Icon = item.icon;
          return (
            <BottomNavigationAction
              key={item.path}
              label={item.label}
              value={item.path}
              icon={<Icon />}
            />
          );
        })}
      </BottomNavigation>
    </Paper>
  );
}
