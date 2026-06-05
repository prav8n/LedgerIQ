import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Box, Drawer, Toolbar, useMediaQuery, useTheme } from '@mui/material';
import { Sidebar } from '@/layouts/Sidebar';
import { Topbar } from '@/layouts/Topbar';
import { BottomNav } from '@/layouts/BottomNav';
import { navItems } from '@/layouts/navItems';

const DRAWER_WIDTH = 248;

export function MainLayout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { pathname } = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const currentTitle =
    navItems.find((item) => pathname.startsWith(item.path))?.label ?? 'LedgerIQ';

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Desktop permanent sidebar */}
      {!isMobile && (
        <Drawer
          variant="permanent"
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              boxSizing: 'border-box',
              borderRight: (t) => `1px solid ${t.palette.divider}`,
            },
          }}
          open
        >
          <Sidebar />
        </Drawer>
      )}

      {/* Mobile temporary drawer */}
      {isMobile && (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{ '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' } }}
        >
          <Sidebar onNavigate={() => setMobileOpen(false)} />
        </Drawer>
      )}

      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <Topbar
          onMenuClick={() => setMobileOpen(true)}
          showMenuButton={isMobile}
          title={currentTitle}
        />
        <Box
          component="main"
          sx={{
            flex: 1,
            p: { xs: 2, sm: 3 },
            pb: isMobile ? 10 : 3, // leave space for the bottom nav
            maxWidth: 1280,
            width: '100%',
            mx: 'auto',
          }}
        >
          <Outlet />
        </Box>
        {isMobile && (
          <>
            <Toolbar />
            <BottomNav />
          </>
        )}
      </Box>
    </Box>
  );
}
