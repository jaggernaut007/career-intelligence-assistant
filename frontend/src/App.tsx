import { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCreateSession } from '@/api/hooks';
import { useSessionStore } from '@/store';
import { WizardContainer } from '@/components/wizard/WizardContainer';
import { Spinner } from '@/components/ui/Spinner';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';

function AppContent() {
  const session = useSessionStore((s) => s.session);
  const isInitializing = useSessionStore((s) => s.isInitializing);
  const error = useSessionStore((s) => s.error);
  const createSession = useCreateSession();

  useEffect(() => {
    if (!session && !isInitializing) {
      createSession.mutate();
    }
  }, [session, isInitializing]);

  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Spinner size="lg" />
          <p className="mt-4 text-gray-600">Initializing session...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full">
          <Alert variant="error" title="Session Error">
            {error}
          </Alert>
          <Button
            className="mt-4 w-full"
            onClick={() => createSession.mutate()}
            isLoading={createSession.isPending}
          >
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Spinner size="lg" />
      </div>
    );
  }

  return <WizardContainer />;
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppContent />} />
    </Routes>
  );
}

export default App;
