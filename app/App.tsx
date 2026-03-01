import 'react-native-gesture-handler';

import React, { useEffect, useMemo, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { ActivityIndicator, View } from 'react-native';

import { AuthContext, UserProfile } from './src/auth/context';
import { getToken, setToken as persistToken, clearToken } from './src/auth/token';
import { LoginScreen } from './src/screens/Login';
import { HomeScreen } from './src/screens/Home';
import { MachineDetailScreen } from './src/screens/MachineDetail';
import { InspectionCaptureScreen } from './src/screens/InspectionCapture';
import { InspectionReportScreen } from './src/screens/InspectionReport';
import { RootStackParamList } from './src/types/navigation';
import { getProfile } from './src/api/auth';
import { MachinesProvider } from './src/machines/MachinesContext';

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  const [token, setTokenState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const stored = await getToken();
        setTokenState(stored);
      } finally {
        setLoading(false);
      }
    };
    bootstrap();
  }, []);

  useEffect(() => {
    if (!token) {
      setUser(null);
      return;
    }
    let cancelled = false;
    const fetchProfile = async () => {
      setProfileLoading(true);
      try {
        const profile = await getProfile();
        if (!cancelled) {
          setUser(profile);
        }
      } catch (error) {
        await clearToken();
        if (!cancelled) {
          setTokenState(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setProfileLoading(false);
        }
      }
    };
    fetchProfile();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const authContext = useMemo(
    () => ({
      token,
      user,
      profileLoading,
      signIn: async (nextToken: string) => {
        await persistToken(nextToken);
        setTokenState(nextToken);
      },
      signOut: async () => {
        await clearToken();
        setTokenState(null);
        setUser(null);
      },
    }),
    [token, user, profileLoading]
  );

  if (loading || (token && profileLoading)) {
    return (
      <View style={{ flex: 1, backgroundColor: '#1B1B1B', alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator size="large" color="#F4D35E" />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <AuthContext.Provider value={authContext}>
        <NavigationContainer>
          {token && user ? (
            <MachinesProvider userId={user.id}>
              <Stack.Navigator screenOptions={{ headerShown: false }}>
                <Stack.Screen name="Home" component={HomeScreen} />
                <Stack.Screen name="MachineDetail" component={MachineDetailScreen} />
                <Stack.Screen name="InspectionCapture" component={InspectionCaptureScreen} />
                <Stack.Screen name="InspectionReport" component={InspectionReportScreen} />
              </Stack.Navigator>
            </MachinesProvider>
          ) : (
            <Stack.Navigator screenOptions={{ headerShown: false }}>
              <Stack.Screen name="Login" component={LoginScreen} />
            </Stack.Navigator>
          )}
        </NavigationContainer>
      </AuthContext.Provider>
      <StatusBar style="light" />
    </SafeAreaProvider>
  );
}
