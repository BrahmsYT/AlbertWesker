'use client';

import * as React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="w-9 h-9" />;
  }

  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex items-center justify-center relative w-9 h-9"
      title="Toggle theme"
    >
      {theme === 'dark' ? (
        <Moon className="h-5 w-5 text-slate-400" />
      ) : (
        <Sun className="h-5 w-5 text-slate-600" />
      )}
      <span className="sr-only">Toggle theme</span>
    </button>
  );
}
