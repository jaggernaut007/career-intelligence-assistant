import { useState, useEffect } from 'react';
import { Key, Lock, Eye, EyeOff, AlertCircle, Sparkles } from 'lucide-react';
import { cn } from '@/utils/cn';
import { apiClient } from '@/api/client';
import { useCreateSession, useSetApiKey, usePasswordLogin } from '@/api/hooks';
import { useSessionStore } from '@/store';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';

type LoginMode = 'password' | 'apikey';

export function LoginScreen() {
  const [mode, setMode] = useState<LoginMode>('password');
  const [input, setInput] = useState('');
  const [showInput, setShowInput] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [authMethods, setAuthMethods] = useState<string[]>([]);

  const createSession = useCreateSession();
  const setApiKeyMutation = useSetApiKey();
  const passwordLoginMutation = usePasswordLogin();

  // Set default mode based on available auth methods
  useEffect(() => {
    if (authMethods.length > 0 && !authMethods.includes(mode)) {
      setMode(authMethods.includes('password') ? 'password' : 'apikey');
    }
  }, [authMethods]);

  const hasMultipleMethods = authMethods.includes('password') && authMethods.includes('apikey');

  const handleLogin = async () => {
    const value = input.trim();
    if (!value) return;

    if (mode === 'apikey' && !value.startsWith('sk-')) {
      setError('Invalid key format. OpenAI API keys start with "sk-".');
      return;
    }

    setError(null);
    setIsLoggingIn(true);

    try {
      // Step 1: Create a new session (returns available auth methods)
      const session = await createSession.mutateAsync();
      if (session.authMethods) {
        setAuthMethods(session.authMethods);
      }

      // Step 2: Authenticate
      if (mode === 'apikey') {
        const result = await setApiKeyMutation.mutateAsync(value);
        if (!result.valid) {
          throw new Error(result.message || 'Invalid API key');
        }
      } else {
        const result = await passwordLoginMutation.mutateAsync(value);
        if (!result.valid) {
          throw new Error(result.message || 'Invalid password');
        }
      }
    } catch (err) {
      setError((err as Error).message);
      // Clean up backend session if it was created
      const currentSession = useSessionStore.getState().session;
      if (currentSession?.sessionId) {
        try {
          await apiClient.delete(`/api/v1/session/${currentSession.sessionId}`);
        } catch {
          // Best-effort cleanup
        }
      }
      useSessionStore.getState().clearSession();
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      handleLogin();
    }
  };

  const switchMode = (newMode: LoginMode) => {
    setMode(newMode);
    setInput('');
    setError(null);
    setShowInput(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Branding */}
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-blue-600 flex items-center justify-center mb-4">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Career Intelligence Assistant</h1>
          <p className="text-gray-500 mt-2">
            AI-powered resume analysis and job matching
          </p>
        </div>

        {/* Login Card */}
        <Card>
          <CardContent className="p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                {mode === 'password' ? (
                  <Lock className="w-5 h-5 text-blue-600" />
                ) : (
                  <Key className="w-5 h-5 text-blue-600" />
                )}
              </div>
              <div>
                <p className="font-medium text-gray-900">Sign In</p>
                <p className="text-sm text-gray-500">
                  {mode === 'password'
                    ? 'Enter your password to get started'
                    : 'Enter your OpenAI API key to get started'}
                </p>
              </div>
            </div>

            {/* Mode Toggle — only show if both methods are available or not yet known */}
            {(hasMultipleMethods || authMethods.length === 0) && (
              <div className="flex rounded-lg bg-gray-100 p-1 mb-5">
                <button
                  type="button"
                  onClick={() => switchMode('password')}
                  className={cn(
                    'flex-1 py-1.5 text-sm font-medium rounded-md transition-colors',
                    mode === 'password'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  )}
                >
                  Password
                </button>
                <button
                  type="button"
                  onClick={() => switchMode('apikey')}
                  className={cn(
                    'flex-1 py-1.5 text-sm font-medium rounded-md transition-colors',
                    mode === 'apikey'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  )}
                >
                  API Key
                </button>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="login-input" className="block text-sm font-medium text-gray-700 mb-1.5">
                  {mode === 'password' ? 'Password' : 'OpenAI API Key'}
                </label>
                <div className="relative">
                  <input
                    id="login-input"
                    type={showInput ? 'text' : 'password'}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={mode === 'password' ? 'Enter password' : 'sk-...'}
                    className={cn(
                      'w-full px-4 py-2.5 pr-10 border rounded-lg text-sm',
                      'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                      'placeholder-gray-400',
                      error ? 'border-red-300' : 'border-gray-300'
                    )}
                    disabled={isLoggingIn}
                    autoFocus
                    aria-label={mode === 'password' ? 'Password' : 'OpenAI API Key'}
                  />
                  <button
                    type="button"
                    onClick={() => setShowInput(!showInput)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    aria-label={showInput ? 'Hide input' : 'Show input'}
                  >
                    {showInput ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={!input.trim() || isLoggingIn}
                isLoading={isLoggingIn}
              >
                {isLoggingIn ? 'Signing in...' : 'Sign In'}
              </Button>

              {error && (
                <Alert variant="error">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{error}</span>
                  </div>
                </Alert>
              )}
            </form>

            <p className="text-xs text-gray-400 mt-4 text-center">
              {mode === 'password'
                ? 'Uses the server-configured API key for this session.'
                : 'Your key is encrypted in memory for this session only. It is never stored permanently.'}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
