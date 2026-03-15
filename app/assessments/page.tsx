'use client';

import { useAuth } from '@/components/auth-provider';
import { DashboardLayout } from '@/components/dashboard-layout';
import { db, handleFirestoreError, OperationType } from '@/lib/firebase';
import { collection, query, where, getDocs, orderBy } from 'firebase/firestore';
import { useEffect, useState } from 'react';
import { FileCheck, Plus, Search, MoreVertical, Clock, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';
import { format } from 'date-fns';

export default function AssessmentsPage() {
  const { organization } = useAuth();
  const [assessments, setAssessments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!organization) return;

    const fetchAssessments = async () => {
      try {
        const q = query(
          collection(db, 'assessments'),
          where('organizationId', '==', organization.id),
          orderBy('createdAt', 'desc')
        );
        const snap = await getDocs(q);
        const data = snap.docs.map(doc => ({ id: doc.id, ...doc.data() }));
        setAssessments(data);
      } catch (error) {
        handleFirestoreError(error, OperationType.LIST, 'assessments');
      } finally {
        setLoading(false);
      }
    };

    fetchAssessments();
  }, [organization]);

  if (!organization) return null;

  return (
    <DashboardLayout>
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Assessments</h1>
          <p className="text-slate-500 dark:text-slate-400">Manage your cybersecurity gap assessments.</p>
        </div>
        <Link href="/assessments/new" className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 transition-colors flex items-center gap-2">
          <Plus className="w-5 h-5" />
          New Assessment
        </Link>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden transition-colors duration-200">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="relative w-full max-w-md">
            <Search className="w-5 h-5 text-slate-400 dark:text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input 
              type="text" 
              placeholder="Search assessments..." 
              className="w-full pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-colors duration-200"
            />
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-500 dark:text-slate-400">Loading assessments...</div>
        ) : assessments.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center">
            <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
              <FileCheck className="w-8 h-8 text-slate-400 dark:text-slate-500" />
            </div>
            <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">No assessments yet</h3>
            <p className="text-slate-500 dark:text-slate-400 mb-6 max-w-sm">Start your first assessment to identify security gaps and generate a remediation roadmap.</p>
            <Link href="/assessments/new" className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 transition-colors">
              Start Assessment
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-800 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold transition-colors duration-200">
                  <th className="p-4">Name</th>
                  <th className="p-4">Frameworks</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Maturity</th>
                  <th className="p-4">Date</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {assessments.map((assessment) => (
                  <tr key={assessment.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors duration-200">
                    <td className="p-4">
                      <Link href={`/assessments/${assessment.id}`} className="font-medium text-indigo-600 dark:text-indigo-400 hover:underline">
                        {assessment.name}
                      </Link>
                    </td>
                    <td className="p-4">
                      <div className="flex gap-1 flex-wrap">
                        {assessment.frameworks.map((f: string) => (
                          <span key={f} className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs rounded-md font-medium">
                            {f}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-1.5">
                        {assessment.status === 'completed' ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
                        ) : (
                          <Clock className="w-4 h-4 text-amber-500 dark:text-amber-400" />
                        )}
                        <span className="text-sm font-medium capitalize text-slate-700 dark:text-slate-300">
                          {assessment.status.replace('_', ' ')}
                        </span>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <div className="w-full max-w-[100px] bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                          <div 
                            className="bg-indigo-600 dark:bg-indigo-500 h-2 rounded-full" 
                            style={{ width: `${assessment.maturityScore || 0}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{assessment.maturityScore || 0}%</span>
                      </div>
                    </td>
                    <td className="p-4 text-sm text-slate-500 dark:text-slate-400">
                      {format(new Date(assessment.createdAt), 'MMM d, yyyy')}
                    </td>
                    <td className="p-4 text-right">
                      <button className="p-2 text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                        <MoreVertical className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
