'use client';

import { useAuth } from '@/components/auth-provider';
import { Shield, ArrowRight, CheckCircle2, Lock, FileText, Activity } from 'lucide-react';
import { motion } from 'motion/react';
import Link from 'next/link';
import { ThemeToggle } from '@/components/theme-toggle';
import { LanguageToggle } from '@/components/language-toggle';
import { useTranslation } from 'react-i18next';

export default function LandingPage() {
  const { user, loading, signIn } = useAuth();
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
      <header className="px-6 py-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 transition-colors duration-200">
        <div className="flex items-center gap-2">
          <Shield className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
          <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">CyberGap AI</span>
        </div>
        <nav className="flex items-center gap-4">
          <LanguageToggle />
          <ThemeToggle />
          {user ? (
            <Link href="/dashboard" className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400">
              {t('common.dashboard')}
            </Link>
          ) : (
            <button
              onClick={signIn}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 transition-colors"
            >
              {t('common.signIn')}
            </button>
          )}
        </nav>
      </header>

      <main className="flex-1">
        <section className="py-24 px-6 text-center max-w-4xl mx-auto">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white mb-6"
          >
            {t('landing.title')}
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-xl text-slate-600 dark:text-slate-400 mb-10 max-w-2xl mx-auto"
          >
            {t('landing.subtitle')}
          </motion.p>
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            {user ? (
              <Link href="/dashboard" className="px-8 py-4 text-lg font-medium text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 transition-colors flex items-center gap-2">
                {t('common.dashboard')} <ArrowRight className="w-5 h-5" />
              </Link>
            ) : (
              <button onClick={signIn} className="px-8 py-4 text-lg font-medium text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 transition-colors flex items-center gap-2">
                {t('common.getStarted')} <ArrowRight className="w-5 h-5" />
              </button>
            )}
          </motion.div>
        </section>

        <section className="py-20 bg-slate-100 dark:bg-slate-900/50 px-6 transition-colors duration-200">
          <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-8">
            <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 transition-colors duration-200">
              <div className="w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-xl flex items-center justify-center mb-6">
                <Activity className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3 text-slate-900 dark:text-white">Gap Assessments</h3>
              <p className="text-slate-600 dark:text-slate-400">Run comprehensive assessments mapped to ISO 27001, NIST, CIS, and Banking Regulations.</p>
            </div>
            <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 transition-colors duration-200">
              <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 rounded-xl flex items-center justify-center mb-6">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3 text-slate-900 dark:text-white">AI Remediation</h3>
              <p className="text-slate-600 dark:text-slate-400">Our AI assistant explains findings, maps controls, and generates 30/60/90-day roadmaps.</p>
            </div>
            <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 transition-colors duration-200">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-xl flex items-center justify-center mb-6">
                <Lock className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3 text-slate-900 dark:text-white">Risk Register</h3>
              <p className="text-slate-600 dark:text-slate-400">Track and manage your cyber risks, assign owners, and monitor remediation progress.</p>
            </div>
          </div>
        </section>
      </main>
      
      <footer className="py-8 text-center text-slate-500 dark:text-slate-400 text-sm border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 transition-colors duration-200">
        &copy; {new Date().getFullYear()} CyberGap AI. All rights reserved.
      </footer>
    </div>
  );
}
