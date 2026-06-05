import CreditCardRoundedIcon from '@mui/icons-material/CreditCardRounded';
import { ModulePlaceholder } from '@/components/ModulePlaceholder';

export function CreditCardsPage() {
  return (
    <ModulePlaceholder
      title="Credit Cards"
      subtitle="Limits, utilization, dues and cashback"
      icon={<CreditCardRoundedIcon />}
    />
  );
}
