import { Box, Card, CardContent, Skeleton, Stack } from '@mui/material';

interface Props {
  /** Number of stat/summary cards to render in the top grid. */
  cards?: number;
  /** Number of list rows to render below. */
  rows?: number;
}

/** Generic page-level loading placeholder. */
export function LoadingSkeleton({ cards = 4, rows = 5 }: Props) {
  return (
    <Box>
      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: {
            xs: '1fr',
            sm: '1fr 1fr',
            md: `repeat(${Math.min(cards, 4)}, 1fr)`,
          },
          mb: 3,
        }}
      >
        {Array.from({ length: cards }).map((_, i) => (
          <Card key={i}>
            <CardContent>
              <Skeleton variant="text" width="55%" />
              <Skeleton variant="text" width="80%" height={36} />
              <Skeleton variant="text" width="40%" />
            </CardContent>
          </Card>
        ))}
      </Box>

      <Card>
        <CardContent>
          <Stack spacing={1.5}>
            {Array.from({ length: rows }).map((_, i) => (
              <Stack key={i} direction="row" alignItems="center" spacing={2}>
                <Skeleton variant="circular" width={40} height={40} />
                <Box flex={1}>
                  <Skeleton variant="text" width="40%" />
                  <Skeleton variant="text" width="25%" />
                </Box>
                <Skeleton variant="text" width={80} />
              </Stack>
            ))}
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
