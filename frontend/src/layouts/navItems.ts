import type { SvgIconComponent } from '@mui/icons-material';
import DashboardRoundedIcon from '@mui/icons-material/DashboardRounded';
import PaymentsRoundedIcon from '@mui/icons-material/PaymentsRounded';
import ReceiptLongRoundedIcon from '@mui/icons-material/ReceiptLongRounded';
import CreditCardRoundedIcon from '@mui/icons-material/CreditCardRounded';
import SavingsRoundedIcon from '@mui/icons-material/SavingsRounded';
import FlagRoundedIcon from '@mui/icons-material/FlagRounded';
import TrendingUpRoundedIcon from '@mui/icons-material/TrendingUpRounded';
import SubscriptionsRoundedIcon from '@mui/icons-material/SubscriptionsRounded';
import AccountBalanceRoundedIcon from '@mui/icons-material/AccountBalanceRounded';
import PieChartRoundedIcon from '@mui/icons-material/PieChartRounded';
import NotificationsRoundedIcon from '@mui/icons-material/NotificationsRounded';
import InsightsRoundedIcon from '@mui/icons-material/InsightsRounded';
import { paths } from '@/routes/paths';

export interface NavItem {
  label: string;
  path: string;
  icon: SvgIconComponent;
}

/** Full navigation list (desktop sidebar). */
export const navItems: NavItem[] = [
  { label: 'Dashboard', path: paths.dashboard, icon: DashboardRoundedIcon },
  { label: 'Income', path: paths.income, icon: PaymentsRoundedIcon },
  { label: 'Expenses', path: paths.expenses, icon: ReceiptLongRoundedIcon },
  { label: 'Credit Cards', path: paths.creditCards, icon: CreditCardRoundedIcon },
  { label: 'Budgets', path: paths.budgets, icon: SavingsRoundedIcon },
  { label: 'Goals', path: paths.goals, icon: FlagRoundedIcon },
  { label: 'Investments', path: paths.investments, icon: TrendingUpRoundedIcon },
  { label: 'Subscriptions', path: paths.subscriptions, icon: SubscriptionsRoundedIcon },
  { label: 'EMIs', path: paths.emis, icon: AccountBalanceRoundedIcon },
  { label: 'Net Worth', path: paths.netWorth, icon: PieChartRoundedIcon },
  { label: 'Notifications', path: paths.notifications, icon: NotificationsRoundedIcon },
  { label: 'Analytics', path: paths.analytics, icon: InsightsRoundedIcon },
];

/** Condensed list for the mobile bottom navigation (max 5). */
export const bottomNavItems: NavItem[] = [
  { label: 'Home', path: paths.dashboard, icon: DashboardRoundedIcon },
  { label: 'Expenses', path: paths.expenses, icon: ReceiptLongRoundedIcon },
  { label: 'Budgets', path: paths.budgets, icon: SavingsRoundedIcon },
  { label: 'Goals', path: paths.goals, icon: FlagRoundedIcon },
  { label: 'Cards', path: paths.creditCards, icon: CreditCardRoundedIcon },
];
