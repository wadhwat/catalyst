import React from 'react';

export type UserProfile = {
  id: number;
  email: string;
  display_name?: string | null;
};

export type AuthContextValue = {
  token: string | null;
  user: UserProfile | null;
  profileLoading: boolean;
  signIn: (token: string) => Promise<void>;
  signOut: () => Promise<void>;
};

export const AuthContext = React.createContext<AuthContextValue>({
  token: null,
  user: null,
  profileLoading: false,
  signIn: async () => {},
  signOut: async () => {},
});
