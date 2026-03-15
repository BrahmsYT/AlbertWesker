'use client';

import { useAuth } from '@/components/auth-provider';
import { DashboardLayout } from '@/components/dashboard-layout';
import { FileText, Download, Eye, BarChart3, ShieldCheck } from 'lucide-react';

export default function ReportsPage() {
  const { organization } = useAuth();

  if (!organization) return null;

  const reports = [
    {
      id: 1,
      title: 'Executive Summary Report',
      description: 'High-level overview of security posture, key risks, and strategic recommendations for board members and executives.',
      icon: BarChart3,
      color: 'text-indigo-600',
      bg: 'bg-indigo-100',
      available: true
    },
    {
      id: 2,
      title: 'Technical Remediation Report',
      description: 'Detailed breakdown of all findings, control mappings, and step-by-step remediation guidance for IT and Security teams.',
      icon: ShieldCheck,
      color: 'text-emerald-600',
      bg: 'bg-emerald-100',
      available: true
    },
    {
      id: 3,
      title: 'Compliance Readiness Report',
      description: 'Gap analysis against selected frameworks (ISO 27001, NIST CSF) showing current compliance percentage.',
      icon: FileText,
      color: 'text-amber-600',
      bg: 'bg-amber-100',
      available: false
    }
  ];

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Reports</h1>
        <p className="text-slate-500 dark:text-slate-400">Generate and download security and compliance reports.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reports.map((report) => (
          <div key={report.id} className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 flex flex-col transition-colors duration-200">
            <div className={`w-12 h-12 ${report.bg} dark:bg-opacity-20 ${report.color} dark:text-opacity-90 rounded-xl flex items-center justify-center mb-6`}>
              <report.icon className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">{report.title}</h3>
            <p className="text-sm text-slate-600 dark:text-slate-300 mb-8 flex-1">{report.description}</p>
            
            <div className="flex items-center gap-3 mt-auto">
              {report.available ? (
                <>
                  <button className="flex-1 px-4 py-2 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors flex items-center justify-center gap-2">
                    <Download className="w-4 h-4" /> Download
                  </button>
                  <button className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors flex items-center justify-center">
                    <Eye className="w-4 h-4" />
                  </button>
                </>
              ) : (
                <button disabled className="w-full px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 rounded-lg font-medium cursor-not-allowed flex items-center justify-center gap-2">
                  Upgrade to Professional
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </DashboardLayout>
  );
}
