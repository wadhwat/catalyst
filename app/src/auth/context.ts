import React from 'react';

export type AuthContextValue = {
  token: string | null;
  signIn: (token: string) => Promise<void>;
  signOut: () => Promise<void>;
};

export const AuthContext = React.createContext<AuthContextValue>({
  token: null,
  signIn: async () => {},
  signOut: async () => {},
});
