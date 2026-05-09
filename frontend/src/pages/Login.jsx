import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { login, register } from '../api';
import { toast } from '@/components/ui/use-toast';

const Login = ({ setIsAuthenticated }) => {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === 'login') {
        await login({ email: form.email, password: form.password });
        setIsAuthenticated(true);
        toast({ title: 'Login successful' });
      } else {
        await register({ username: form.username, email: form.email, password: form.password });
        toast({ title: 'Account created — please log in' });
        setMode('login');
        setForm((f) => ({ ...f, password: '' }));
      }
    } catch {
      // errors shown by api.js
    }
    setLoading(false);
  };

  return (
    <Card className="mx-auto max-w-md mt-20">
      <CardHeader>
        <CardTitle>{mode === 'login' ? 'Log In' : 'Create Account'}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <div>
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={form.username}
                onChange={set('username')}
                minLength={3}
                maxLength={50}
                required
              />
            </div>
          )}
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={form.email}
              onChange={set('email')}
              required
            />
          </div>
          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={form.password}
              onChange={set('password')}
              minLength={mode === 'register' ? 8 : undefined}
              required
            />
            {mode === 'register' && (
              <p className="text-xs text-muted-foreground mt-1">Minimum 8 characters</p>
            )}
          </div>
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? (mode === 'login' ? 'Logging in…' : 'Creating account…') : (mode === 'login' ? 'Log In' : 'Create Account')}
          </Button>
        </form>
        <p className="text-center text-sm mt-4 text-muted-foreground">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button
            type="button"
            className="underline text-foreground"
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setForm({ username: '', email: '', password: '' }); }}
          >
            {mode === 'login' ? 'Register' : 'Log In'}
          </button>
        </p>
      </CardContent>
    </Card>
  );
};

export default Login;
