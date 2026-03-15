'use client';

import { useAuth } from '@/components/auth-provider';
import { DashboardLayout } from '@/components/dashboard-layout';
import { db } from '@/lib/firebase';
import { collection, query, where, getDocs } from 'firebase/firestore';
import { useEffect, useState } from 'react';
import { ShieldAlert, CheckCircle, Activity, AlertCircle } from 'lucide-react';
import { motion } from 'motion/react';
import Link from 'next/link';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useTheme } from 'next-themes';
import { useTranslation } from 'react-i18next';

export default function DashboardPage() {
  const { organization } = useAuth();
  const { theme } = useTheme();
  const { t } = useTranslation();
  const [stats, setStats] = useState({
    assessments: 0,
    openFindings: 0,
    criticalFindings: 0,
    openActions: 0,
    maturityScore: 0,
    riskScore: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!organization) return;

    const fetchStats = async () => {
      try {
        const assessmentsQ = query(collection(db, 'assessments'), where('organizationId', '==', organization.id));
        const findingsQ = query(collection(db, 'findings'), where('organizationId', '==', organization.id), where('status', 'in', ['open', 'in_progress']));
        const actionsQ = query(collection(db, 'actions'), where('organizationId', '==', organization.id), where('status', 'in', ['open', 'in_progress', 'blocked']));

        const [assessmentsSnap, findingsSnap, actionsSnap] = await Promise.all([
          getDocs(assessmentsQ),
          getDocs(findingsQ),
          getDocs(actionsQ)
        ]);

        let criticalCount = 0;
        findingsSnap.forEach(doc => {
          if (doc.data().severity === 'Critical') criticalCount++;
        });

        let totalMaturity = 0;
        let completedAssessments = 0;
        assessmentsSnap.forEach(doc => {
          if (doc.data().status === 'completed') {
            totalMaturity += doc.data().maturityScore || 0;
            completedAssessments++;
          }
        });

        const avgMaturity = completedAssessments > 0 ? Math.round(totalMaturity / completedAssessments) : 0;
        const riskScore = Math.min(100, (criticalCount * 10) + (findingsSnap.size * 2));

        setStats({
          assessments: assessmentsSnap.size,
          openFindings: findingsSnap.size,
          criticalFindings: criticalCount,
          openActions: actionsSnap.size,
          maturityScore: avgMaturity,
          riskScore: riskScore,
        });
      } catch (error) {
        console.error('Error fetching dashboard stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [organization]);

  if (!organization) return null;

  const chartData = [
    { name: 'Gov', score: 65 },
    { name: 'IAM', score: 40 },
    { name: 'Net', score: 80 },
    { name: 'App', score: 55 },
    { name: 'Data', score: 70 },
  ];

  const isDark = theme === 'dark';
  const gridColor = isDark ? '#334155' : '#e2e8f0';
  const textColor = isDark ? '#94a3b8' : '#64748b';
  const tooltipBg = isDark ? '#1e293b' : '#f1f5f9';

  return (
    <DashboardLayout>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{t('common.dashboard')}</h1>
          <p className="text-slate-500 dark:text-slate-400">{t('common.welcome', { type: organization.type })}</p>
        </div>
        <Link href="/assessments/new" className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 transition-colors">
          {t('common.newAssessment')}
        </Link>
      </div>

      {loading ? (
        <div className="animate-pulse grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-32 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400">Overall Risk Score</h3>
              <Activity className={`w-5 h-5 ${stats.riskScore > 70 ? 'text-red-500' : stats.riskScore > 40 ? 'text-amber-500' : 'text-emerald-500'}`} />
            </div>
            <div className="text-3xl font-bold text-slate-900 dark:text-white">{stats.riskScore}/100</div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Lower is better</p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400">Maturity Score</h3>
              <CheckCircle className="w-5 h-5 text-indigo-500 dark:text-indigo-400" />
            </div>
            <div className="text-3xl font-bold text-slate-900 dark:text-white">{stats.maturityScore}%</div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Average across assessments</p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400">Open Findings</h3>
              <AlertCircle className="w-5 h-5 text-amber-500" />
            </div>
            <div className="text-3xl font-bold text-slate-900 dark:text-white">{stats.openFindings}</div>
            <p className="text-xs text-red-500 dark:text-red-400 mt-1 font-medium">{stats.criticalFindings} Critical</p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400">Remediation Actions</h3>
              <ShieldAlert className="w-5 h-5 text-blue-500 dark:text-blue-400" />
            </div>
            <div className="text-3xl font-bold text-slate-900 dark:text-white">{stats.openActions}</div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Pending completion</p>
          </motion.div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200">
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-6">Maturity by Domain</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridColor} />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: textColor, fontSize: 12 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: textColor, fontSize: 12 }} />
                <Tooltip cursor={{ fill: tooltipBg }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', backgroundColor: isDark ? '#1e293b' : '#ffffff', color: isDark ? '#f8fafc' : '#0f172a' }} />
                <Bar dataKey="score" fill="#4f46e5" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Recent Activity</h3>
            <Link href="/actions" className="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300">View All</Link>
          </div>
          <div className="space-y-4">
            {stats.assessments === 0 ? (
              <div className="text-center py-8">
                <p className="text-slate-500 dark:text-slate-400 mb-4">No activity yet.</p>
                <Link href="/assessments/new" className="text-indigo-600 dark:text-indigo-400 font-medium hover:underline">Start your first assessment</Link>
              </div>
            ) : (
              <div className="text-sm text-slate-600 dark:text-slate-300">
                <p className="py-2 border-b border-slate-100 dark:border-slate-800">Assessment &quot;Initial Baseline&quot; created.</p>
                <p className="py-2 border-b border-slate-100 dark:border-slate-800">3 critical findings identified in Network Security.</p>
                <p className="py-2 border-b border-slate-100 dark:border-slate-800">AI Roadmap generated for Q3.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
