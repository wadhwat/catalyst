import { apiFetch } from './client';

export type LoginResponse = {
  access_token: string;
};

export async function login(email: string, password: string): Promise<LoginResponse> {
  return apiFetch<LoginResponse>(
    '/auth/login',
    {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    },
    false
  );
}
