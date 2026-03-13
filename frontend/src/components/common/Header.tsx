import { LogOut, Sparkles } from 'lucide-react';
import { useSessionStore } from '@/store';
import { useLogout } from '@/api/hooks';
import { Button } from '@/components/ui/Button';

export function Header() {
  const session = useSessionStore((s) => s.session);
  const logoutMutation = useLogout();

  if (!session) return null;

  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-gray-900 text-sm">
            Career Intelligence
          </span>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => logoutMutation.mutate()}
          disabled={logoutMutation.isPending}
          className="text-gray-500 hover:text-red-600"
        >
          <LogOut className="w-4 h-4 mr-1.5" />
          {logoutMutation.isPending ? 'Logging out...' : 'Logout'}
        </Button>
      </div>
    </header>
  );
}
