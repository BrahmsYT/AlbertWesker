'use client';

import { useAuth } from '@/components/auth-provider';
import { DashboardLayout } from '@/components/dashboard-layout';
import { db, handleFirestoreError, OperationType } from '@/lib/firebase';
import { doc, getDoc, collection, query, where, getDocs } from 'firebase/firestore';
import { useEffect, useState, use } from 'react';
import { CheckCircle2, AlertTriangle, ArrowRight, Activity, FileText } from 'lucide-react';
import Link from 'next/link';

export default function AssessmentResultsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const { organization } = useAuth();
  const [assessment, setAssessment] = useState<any>(null);
  const [findings, setFindings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!organization) return;

    const fetchResults = async () => {
      try {
        const docRef = doc(db, 'assessments', resolvedParams.id);
        const docSnap = await getDoc(docRef);
        
        if (docSnap.exists() && docSnap.data().organizationId === organization.id) {
          setAssessment({ id: docSnap.id, ...docSnap.data() });

          const findingsQ = query(
            collection(db, 'findings'),
            where('assessmentId', '==', resolvedParams.id)
          );
          const findingsSnap = await getDocs(findingsQ);
          const findingsData = findingsSnap.docs.map(d => ({ id: d.id, ...d.data() }));
          setFindings(findingsData);
        }
      } catch (error) {
        handleFirestoreError(error, OperationType.GET, 'assessments');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [organization, resolvedParams.id]);

  if (!organization || loading) return <DashboardLayout><div className="p-8">Loading...</div></DashboardLayout>;
  if (!assessment) return <DashboardLayout><div className="p-8">Assessment not found.</div></DashboardLayout>;

  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto">
        <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 px-2 py-1 rounded flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Completed
              </span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{assessment.name} - Results</h1>
          </div>
          <div className="flex gap-3">
            <Link href="/reports" className="px-4 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 rounded-lg font-medium hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2">
              <FileText className="w-4 h-4" /> View Report
            </Link>
            <Link href="/ai" className="px-4 py-2 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors flex items-center gap-2">
              Generate Roadmap <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 flex flex-col items-center justify-center text-center transition-colors duration-200">
            <div className="w-16 h-16 bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 rounded-full flex items-center justify-center mb-4">
              <Activity className="w-8 h-8" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-1">Maturity Score</h2>
            <div className="text-5xl font-extrabold text-indigo-600 dark:text-indigo-400 mb-2">{assessment.maturityScore}%</div>
            <p className="text-sm text-slate-500 dark:text-slate-400">Based on implemented controls across selected frameworks.</p>
          </div>

          <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 flex flex-col items-center justify-center text-center transition-colors duration-200">
            <div className="w-16 h-16 bg-amber-100 dark:bg-amber-900/50 text-amber-600 dark:text-amber-400 rounded-full flex items-center justify-center mb-4">
              <AlertTriangle className="w-8 h-8" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-1">Identified Gaps</h2>
            <div className="text-5xl font-extrabold text-amber-600 dark:text-amber-400 mb-2">{findings.length}</div>
            <p className="text-sm text-slate-500 dark:text-slate-400">Security findings that require remediation.</p>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden transition-colors duration-200">
          <div className="p-6 border-b border-slate-200 dark:border-slate-800">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Assessment Findings</h3>
          </div>
          {findings.length === 0 ? (
            <div className="p-8 text-center text-slate-500 dark:text-slate-400">No findings generated. Excellent security posture!</div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {findings.map((finding) => (
                <div key={finding.id} className="p-6 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-0.5 text-xs font-bold rounded border ${
                          finding.severity === 'High' ? 'bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800' : 'bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800'
                        }`}>
                          {finding.severity}
                        </span>
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">{finding.domain}</span>
                      </div>
                      <h4 className="font-semibold text-slate-900 dark:text-white mb-1">{finding.title}</h4>
                      <p className="text-sm text-slate-600 dark:text-slate-300 mb-3 whitespace-pre-wrap">{finding.description}</p>
                      
                      <div className="flex items-center gap-2">
                        {finding.frameworkMapping.map((f: string) => (
                          <span key={f} className="text-[10px] font-medium uppercase tracking-wider bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 px-1.5 py-0.5 rounded">
                            {f}
                          </span>
                        ))}
                      </div>
                    </div>
                    <Link href={`/findings/${finding.id}`} className="px-3 py-1.5 text-sm font-medium text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors whitespace-nowrap">
                      View Details
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
