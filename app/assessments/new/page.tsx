'use client';

import { useState } from 'react';
import { useAuth } from '@/components/auth-provider';
import { DashboardLayout } from '@/components/dashboard-layout';
import { useRouter } from 'next/navigation';
import { doc, setDoc, collection } from 'firebase/firestore';
import { db, handleFirestoreError, OperationType } from '@/lib/firebase';
import { FileCheck, Shield, ChevronRight } from 'lucide-react';
import { motion } from 'motion/react';

const FRAMEWORKS = [
  { id: 'ISO27001', name: 'ISO 27001', desc: 'International standard for information security management.' },
  { id: 'NIST_CSF', name: 'NIST CSF', desc: 'Cybersecurity framework for critical infrastructure.' },
  { id: 'CIS_CONTROLS', name: 'CIS Controls', desc: 'Prioritized set of actions for cyber defense.' },
  { id: 'BANK_REG', name: 'Bank Regulatory Baseline', desc: 'Stricter controls for financial institutions.' },
];

export default function NewAssessmentPage() {
  const { user, organization } = useAuth();
  const router = useRouter();
  const [name, setName] = useState('');
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const toggleFramework = (id: string) => {
    setSelectedFrameworks(prev => 
      prev.includes(id) ? prev.filter(f => f !== id) : [...prev, id]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !organization || selectedFrameworks.length === 0 || !name) return;
    setLoading(true);

    try {
      const assessmentRef = doc(collection(db, 'assessments'));
      await setDoc(assessmentRef, {
        organizationId: organization.id,
        name,
        frameworks: selectedFrameworks,
        status: 'draft',
        score: 0,
        maturityScore: 0,
        createdBy: user.uid,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      router.push(`/assessments/${assessmentRef.id}`);
    } catch (error) {
      handleFirestoreError(error, OperationType.CREATE, 'assessments');
    } finally {
      setLoading(false);
    }
  };

  if (!organization) return null;

  return (
    <DashboardLayout>
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">New Assessment</h1>
          <p className="text-slate-500 dark:text-slate-400">Create a new gap analysis assessment for {organization.name}.</p>
        </div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-8 transition-colors duration-200"
        >
          <form onSubmit={handleSubmit} className="space-y-8">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Assessment Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-3 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500 transition-colors duration-200"
                placeholder="e.g., Q3 2026 Security Baseline"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-4">Select Frameworks</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {FRAMEWORKS.map((framework) => {
                  const isSelected = selectedFrameworks.includes(framework.id);
                  // If org is Bank, pre-select or highlight Bank Reg
                  const isRecommended = organization.type === 'Bank' && framework.id === 'BANK_REG';

                  return (
                    <div
                      key={framework.id}
                      onClick={() => toggleFramework(framework.id)}
                      className={`p-4 border rounded-xl cursor-pointer transition-all ${
                        isSelected 
                          ? 'border-indigo-600 dark:border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 ring-1 ring-indigo-600 dark:ring-indigo-500' 
                          : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 bg-white dark:bg-slate-900'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-5 h-5 rounded border flex items-center justify-center ${
                            isSelected ? 'bg-indigo-600 dark:bg-indigo-500 border-indigo-600 dark:border-indigo-500' : 'border-slate-300 dark:border-slate-600'
                          }`}>
                            {isSelected && <FileCheck className="w-3.5 h-3.5 text-white" />}
                          </div>
                          <div>
                            <h3 className={`font-medium ${isSelected ? 'text-indigo-900 dark:text-indigo-300' : 'text-slate-900 dark:text-white'}`}>
                              {framework.name}
                            </h3>
                            <p className={`text-xs mt-1 ${isSelected ? 'text-indigo-700 dark:text-indigo-400' : 'text-slate-500 dark:text-slate-400'}`}>
                              {framework.desc}
                            </p>
                          </div>
                        </div>
                      </div>
                      {isRecommended && !isSelected && (
                        <div className="mt-3 text-xs font-medium text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/30 px-2 py-1 rounded inline-flex items-center gap-1">
                          <Shield className="w-3 h-3" /> Recommended for Banks
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="pt-6 border-t border-slate-200 dark:border-slate-800 flex justify-end">
              <button
                type="submit"
                disabled={loading || !name || selectedFrameworks.length === 0}
                className="bg-indigo-600 dark:bg-indigo-500 text-white px-6 py-3 rounded-xl font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 disabled:opacity-50 transition-colors flex items-center gap-2"
              >
                {loading ? 'Creating...' : 'Create Assessment'}
                {!loading && <ChevronRight className="w-5 h-5" />}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </DashboardLayout>
  );
}
