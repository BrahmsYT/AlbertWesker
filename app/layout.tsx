import type {Metadata} from 'next';
import './globals.css';
import { AuthProvider } from '@/components/auth-provider';
import { ErrorBoundary } from '@/components/error-boundary';
import { ThemeProvider } from '@/components/theme-provider';
import { I18nProvider } from '@/components/i18n-provider';

export const metadata: Metadata = {
  title: 'CyberGap AI',
  description: 'AI-powered Cybersecurity Gap Analysis + GRC SaaS platform for banks and companies.',
};

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 font-sans antialiased transition-colors duration-200">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <ErrorBoundary>
            <I18nProvider>
              <AuthProvider>
                {children}
              </AuthProvider>
            </I18nProvider>
          </ErrorBoundary>
        </ThemeProvider>
      </body>
    </html>
  );
}
