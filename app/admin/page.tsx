'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/components/auth-provider';
import { DashboardLayout } from '@/components/dashboard-layout';
import { db, handleFirestoreError, OperationType } from '@/lib/firebase';
import { collection, query, getDocs, doc, updateDoc, orderBy, limit } from 'firebase/firestore';
import { Users, Building2, MessageSquare, CheckCircle, Clock, AlertCircle, Filter, Search, ChevronRight, ExternalLink, Loader2 } from 'lucide-react';
import { motion } from 'motion/react';
import { useTranslation } from 'react-i18next';
import { useRouter } from 'next/navigation';

export default function AdminPanel() {
  const { globalRole, loading: authLoading } = useAuth();
  const { t } = useTranslation();
  const router = useRouter();
  const [stats, setStats] = useState({
    users: 0,
    organizations: 0,
    feedbacks: 0,
  });
  const [feedbacks, setFeedbacks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    if (!authLoading && globalRole !== 'admin') {
      router.push('/dashboard');
    }
  }, [globalRole, authLoading, router]);

  useEffect(() => {
    if (globalRole !== 'admin') return;

    const fetchData = async () => {
      try {
        // Fetch stats
        const usersSnap = await getDocs(collection(db, 'users'));
        const orgsSnap = await getDocs(collection(db, 'organizations'));
        const feedbacksSnap = await getDocs(collection(db, 'feedbacks'));

        setStats({
          users: usersSnap.size,
          organizations: orgsSnap.size,
          feedbacks: feedbacksSnap.size,
        });

        // Fetch feedbacks
        const q = query(collection(db, 'feedbacks'), orderBy('createdAt', 'desc'), limit(50));
        const fbSnap = await getDocs(q);
        setFeedbacks(fbSnap.docs.map(doc => ({ id: doc.id, ...doc.data() })));
      } catch (error) {
        handleFirestoreError(error, OperationType.LIST, 'admin_data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [globalRole]);

  const updateFeedbackStatus = async (id: string, newStatus: string) => {
    try {
      await updateDoc(doc(db, 'feedbacks', id), { status: newStatus });
      setFeedbacks(prev => prev.map(f => f.id === id ? { ...f, status: newStatus } : f));
    } catch (error) {
      handleFirestoreError(error, OperationType.UPDATE, `feedbacks/${id}`);
    }
  };

  if (authLoading || globalRole !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const filteredFeedbacks = feedbacks.filter(f => filter === 'all' || f.status === filter);

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Admin Panel</h1>
        <p className="text-slate-500 dark:text-slate-400">Platform-wide overview and management.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-xl">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Total Users</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">{stats.users}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-xl">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Organizations</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">{stats.organizations}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 rounded-xl">
              <MessageSquare className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Feedbacks</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">{stats.feedbacks}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Feedbacks Section */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">User Feedbacks</h2>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="bg-slate-50 dark:bg-slate-800 border-none rounded-lg text-sm px-3 py-1.5 outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All Status</option>
              <option value="new">New</option>
              <option value="reviewed">Reviewed</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800/50">
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">User</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Content</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Category</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <Loader2 className="w-8 h-8 animate-spin mx-auto text-indigo-600" />
                  </td>
                </tr>
              ) : filteredFeedbacks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                    No feedbacks found.
                  </td>
                </tr>
              ) : (
                filteredFeedbacks.map((fb) => (
                  <tr key={fb.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-slate-900 dark:text-white">{fb.userEmail}</div>
                      <div className="text-xs text-slate-500">{fb.userId.substring(0, 8)}...</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-slate-600 dark:text-slate-300 max-w-xs truncate" title={fb.content}>
                        {fb.content}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        fb.category === 'Bug' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                        fb.category === 'Feature Request' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                        fb.category === 'Improvement' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' :
                        'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400'
                      }`}>
                        {fb.category}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`flex items-center gap-1.5 text-xs font-medium ${
                        fb.status === 'new' ? 'text-blue-600 dark:text-blue-400' :
                        fb.status === 'reviewed' ? 'text-amber-600 dark:text-amber-400' :
                        'text-emerald-600 dark:text-emerald-400'
                      }`}>
                        {fb.status === 'new' ? <Clock className="w-3 h-3" /> :
                         fb.status === 'reviewed' ? <AlertCircle className="w-3 h-3" /> :
                         <CheckCircle className="w-3 h-3" />}
                        {fb.status.charAt(0).toUpperCase() + fb.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-500">
                      {new Date(fb.createdAt).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {fb.status !== 'reviewed' && fb.status !== 'resolved' && (
                          <button
                            onClick={() => updateFeedbackStatus(fb.id, 'reviewed')}
                            className="p-1.5 hover:bg-amber-100 dark:hover:bg-amber-900/30 text-amber-600 rounded-lg transition-colors"
                            title="Mark as Reviewed"
                          >
                            <AlertCircle className="w-4 h-4" />
                          </button>
                        )}
                        {fb.status !== 'resolved' && (
                          <button
                            onClick={() => updateFeedbackStatus(fb.id, 'resolved')}
                            className="p-1.5 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 text-emerald-600 rounded-lg transition-colors"
                            title="Mark as Resolved"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </DashboardLayout>
  );
}
