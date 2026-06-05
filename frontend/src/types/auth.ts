// API shapes mirror the backend Pydantic schemas (snake_case over the wire).

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  phone: string | null;
  currency: string;
  locale: string;
  timezone: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
  phone?: string;
}

export interface ApiError {
  detail: string;
}
