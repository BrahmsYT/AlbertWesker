'use client';

import { useAuth } from '@/components/auth-provider';
import { Shield, LayoutDashboard, FileCheck, AlertTriangle, ListTodo, FileText, Settings, LogOut, Bot, Activity, Settings2, MessageSquare } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ThemeToggle } from '@/components/theme-toggle';
import { LanguageToggle } from '@/components/language-toggle';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { FeedbackModal } from '@/components/feedback-modal';

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, organization, logOut, globalRole } = useAuth();
  const pathname = usePathname();
  const { t } = useTranslation();
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);

  if (!user || (!organization && globalRole !== 'admin')) return null;

  const navigation = [
    { name: t('common.dashboard'), href: '/dashboard', icon: LayoutDashboard },
    { name: t('common.assessments'), href: '/assessments', icon: FileCheck },
    { name: t('common.scan'), href: '/scan', icon: Activity },
    { name: t('common.findings'), href: '/findings', icon: AlertTriangle },
    { name: t('common.risks'), href: '/risks', icon: Shield },
    { name: t('common.actions'), href: '/actions', icon: ListTodo },
    { name: t('common.ai'), href: '/ai', icon: Bot },
    { name: t('common.reports'), href: '/reports', icon: FileText },
    { name: t('common.settings'), href: '/settings', icon: Settings },
  ];

  if (globalRole === 'admin') {
    navigation.push({ name: 'Admin Panel', href: '/admin', icon: Settings2 });
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex transition-colors duration-200">
      {/* Sidebar */}
      <aside className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col fixed h-full transition-colors duration-200">
        <div className="h-16 flex items-center px-6 border-b border-slate-200 dark:border-slate-800">
          <Shield className="w-6 h-6 text-indigo-600 dark:text-indigo-400 mr-2" />
          <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">CyberGap AI</span>
        </div>
        
        <div className="p-4 border-b border-slate-200 dark:border-slate-800">
          <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Workspace</div>
          <div className="font-medium text-slate-900 dark:text-white truncate">{organization?.name || 'Platform Admin'}</div>
          {organization && (
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1">
              <span className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-slate-600 dark:text-slate-300">{organization.type}</span>
              <span className="px-1.5 py-0.5 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded">{organization.subscriptionPlan}</span>
            </div>
          )}
        </div>

        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  isActive 
                    ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' 
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <item.icon className={`w-5 h-5 mr-3 ${isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400 dark:text-slate-500'}`} />
                {item.name}
              </Link>
            );
          })}
          
          <button
            onClick={() => setIsFeedbackOpen(true)}
            className="flex items-center w-full px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          >
            <MessageSquare className="w-5 h-5 mr-3 text-slate-400 dark:text-slate-500" />
            {t('common.feedback', 'Feedback')}
          </button>
        </nav>

        <div className="p-4 border-t border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center overflow-hidden">
              <img src={user.photoURL || `https://ui-avatars.com/api/?name=${user.email}`} alt="" className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700" />
              <div className="ml-3 overflow-hidden">
                <p className="text-sm font-medium text-slate-900 dark:text-white truncate">{user.displayName || 'User'}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{user.email}</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <LanguageToggle />
              <ThemeToggle />
            </div>
          </div>
          <button
            onClick={logOut}
            className="flex items-center w-full px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <LogOut className="w-5 h-5 mr-3 text-slate-400 dark:text-slate-500" />
            {t('common.signOut')}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 flex flex-col min-h-screen">
        <div className="flex-1 p-8">
          {children}
        </div>
      </main>

      <FeedbackModal isOpen={isFeedbackOpen} onClose={() => setIsFeedbackOpen(false)} />
    </div>
  );
}
