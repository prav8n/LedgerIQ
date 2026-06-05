"""Domain enumerations shared across models and (later) schemas.

These are ``str`` enums so they serialize cleanly to JSON. In the database we
render them as ``VARCHAR`` + ``CHECK`` constraints (``native_enum=False``)
which keeps migrations portable between PostgreSQL and SQLite.
"""

from __future__ import annotations

import enum


class IncomeCategory(str, enum.Enum):
    SALARY = "salary"
    BONUS = "bonus"
    FREELANCE = "freelance"
    BUSINESS = "business"
    RENTAL = "rental"
    INTEREST = "interest"
    DIVIDEND = "dividend"
    CAPITAL_GAINS = "capital_gains"
    GIFT = "gift"
    REFUND = "refund"
    OTHER = "other"


class Frequency(str, enum.Enum):
    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ExpenseCategory(str, enum.Enum):
    FOOD = "food"
    GROCERIES = "groceries"
    TRANSPORT = "transport"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    RENT = "rent"
    HEALTH = "health"
    EDUCATION = "education"
    TRAVEL = "travel"
    INSURANCE = "insurance"
    INVESTMENT = "investment"
    EMI = "emi"
    SUBSCRIPTION = "subscription"
    PERSONAL_CARE = "personal_care"
    GIFTS = "gifts"
    TAXES = "taxes"
    FEES = "fees"
    OTHER = "other"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    UPI = "upi"
    DEBIT_CARD = "debit_card"
    CREDIT_CARD = "credit_card"
    NET_BANKING = "net_banking"
    WALLET = "wallet"
    AUTO_DEBIT = "auto_debit"
    OTHER = "other"


class CardNetwork(str, enum.Enum):
    VISA = "visa"
    MASTERCARD = "mastercard"
    RUPAY = "rupay"
    AMEX = "amex"
    DINERS = "diners"
    OTHER = "other"


class CardRewardType(str, enum.Enum):
    CASHBACK = "cashback"
    POINTS = "points"
    MILES = "miles"
    NONE = "none"


class RewardType(str, enum.Enum):
    """Type of reward a single reward rule produces."""

    CASHBACK = "cashback"
    REWARD_POINTS = "reward_points"
    AIR_MILES = "air_miles"
    MILESTONE_BONUS = "milestone_bonus"
    LOUNGE_ACCESS = "lounge_access"
    FEE_WAIVER = "fee_waiver"
    VOUCHER = "voucher"


class RewardAppliesTo(str, enum.Enum):
    """What spend a reward rule applies to."""

    ONLINE = "online"
    OFFLINE = "offline"
    UPI = "upi"
    MERCHANT_SPECIFIC = "merchant_specific"
    CATEGORY_SPECIFIC = "category_specific"
    ALL = "all"


class BudgetPeriod(str, enum.Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class GoalCategory(str, enum.Enum):
    EMERGENCY_FUND = "emergency_fund"
    VACATION = "vacation"
    HOME = "home"
    CAR = "car"
    EDUCATION = "education"
    WEDDING = "wedding"
    GADGET = "gadget"
    RETIREMENT = "retirement"
    INVESTMENT = "investment"
    OTHER = "other"


class GoalStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InvestmentType(str, enum.Enum):
    STOCKS = "stocks"
    MUTUAL_FUNDS = "mutual_funds"
    ETF = "etf"
    FIXED_DEPOSIT = "fixed_deposit"
    RECURRING_DEPOSIT = "recurring_deposit"
    PPF = "ppf"
    EPF = "epf"
    NPS = "nps"
    BONDS = "bonds"
    GOLD = "gold"
    REAL_ESTATE = "real_estate"
    CRYPTO = "crypto"
    OTHER = "other"


class SubscriptionCategory(str, enum.Enum):
    STREAMING = "streaming"
    MUSIC = "music"
    SOFTWARE = "software"
    CLOUD = "cloud"
    NEWS = "news"
    FITNESS = "fitness"
    GAMING = "gaming"
    UTILITIES = "utilities"
    EDUCATION = "education"
    OTHER = "other"


class LoanType(str, enum.Enum):
    HOME = "home"
    CAR = "car"
    PERSONAL = "personal"
    EDUCATION = "education"
    BUSINESS = "business"
    GOLD = "gold"
    CREDIT_CARD = "credit_card"
    OTHER = "other"


class NotificationType(str, enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ALERT = "alert"
    REMINDER = "reminder"


class NotificationCategory(str, enum.Enum):
    BILL = "bill"
    BUDGET = "budget"
    GOAL = "goal"
    EMI = "emi"
    SUBSCRIPTION = "subscription"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"
    INSIGHT = "insight"
    SYSTEM = "system"
