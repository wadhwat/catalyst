import React, { useContext, useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { AuthContext } from '../auth/context';
import { login } from '../api/auth';

export function LoginScreen() {
  const { signIn } = useContext(AuthContext);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Missing details', 'Enter your email and password.');
      return;
    }
    setLoading(true);
    try {
      const response = await login(email, password);
      await signIn(response.access_token);
    } catch (error) {
      Alert.alert('Login failed', String(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.logoBlock}>
          <Text style={styles.logoText}>CAT</Text>
        </View>
        <Text style={styles.title}>CATalyst Inspect</Text>
        <Text style={styles.subtitle}>Fleet Management & Inspection</Text>
      </View>

      <View style={styles.form}>
        <Text style={styles.label}>Email</Text>
        <TextInput
          value={email}
          onChangeText={setEmail}
          placeholder="your.email@example.com"
          placeholderTextColor="#6B7280"
          autoCapitalize="none"
          keyboardType="email-address"
          style={styles.input}
        />

        <Text style={styles.label}>Password</Text>
        <TextInput
          value={password}
          onChangeText={setPassword}
          placeholder="Enter your password"
          placeholderTextColor="#6B7280"
          secureTextEntry
          style={styles.input}
        />

        <TouchableOpacity
          onPress={handleLogin}
          disabled={loading}
          style={[styles.button, loading && { opacity: 0.7 }]}
        >
          {loading ? (
            <ActivityIndicator color="#1B1B1B" />
          ) : (
            <Text style={styles.buttonText}>Log in</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1B1B1B',
    paddingHorizontal: 20,
    paddingTop: 60,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logoBlock: {
    width: 72,
    height: 72,
    borderRadius: 18,
    backgroundColor: '#F4D35E',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  logoText: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1B1B1B',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  subtitle: {
    fontSize: 13,
    color: '#9CA3AF',
    marginTop: 6,
  },
  form: {
    gap: 16,
  },
  label: {
    color: '#D1D5DB',
    fontSize: 13,
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#2A2A2A',
    borderColor: '#3A3A3A',
    borderWidth: 1,
    borderRadius: 12,
    color: '#FFFFFF',
    height: 48,
    paddingHorizontal: 12,
    marginBottom: 8,
  },
  button: {
    backgroundColor: '#F4D35E',
    borderRadius: 16,
    height: 54,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#1B1B1B',
    fontWeight: '700',
    fontSize: 16,
  },
});
