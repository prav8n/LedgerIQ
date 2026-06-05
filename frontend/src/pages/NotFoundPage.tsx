import { useNavigate } from 'react-router-dom';
import { Box, Button, Stack, Typography } from '@mui/material';
import { paths } from '@/routes/paths';

export function NotFoundPage() {
  const navigate = useNavigate();
  return (
    <Box sx={{ display: 'grid', placeItems: 'center', minHeight: '100vh', p: 3 }}>
      <Stack spacing={2} alignItems="center" textAlign="center">
        <Typography variant="h1" fontWeight={800} color="primary.main">
          404
        </Typography>
        <Typography variant="h5">Page not found</Typography>
        <Typography variant="body2" color="text.secondary">
          The page you&apos;re looking for doesn&apos;t exist or has moved.
        </Typography>
        <Button variant="contained" onClick={() => navigate(paths.dashboard)}>
          Back to dashboard
        </Button>
      </Stack>
    </Box>
  );
}
