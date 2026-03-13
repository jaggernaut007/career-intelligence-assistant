import { useSessionStore } from '@/store';
import { WizardContainer } from '@/components/wizard/WizardContainer';
import { LoginScreen } from '@/components/common/LoginScreen';
import { Header } from '@/components/common/Header';
import { Spinner } from '@/components/ui/Spinner';
import { Routes, Route } from 'react-router-dom';

function AppContent() {
  const session = useSessionStore((s) => s.session);
  const apiKeyValidated = useSessionStore((s) => s.apiKeyValidated);
  const isInitializing = useSessionStore((s) => s.isInitializing);

  // Show login screen if no session or API key not validated
  if (!session || !apiKeyValidated) {
    if (isInitializing) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <Spinner size="lg" />
            <p className="mt-4 text-gray-600">Signing in...</p>
          </div>
        </div>
      );
    }
    return <LoginScreen />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <WizardContainer />
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppContent />} />
    </Routes>
  );
}

export default App;
