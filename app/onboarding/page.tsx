'use client';

import { useState } from 'react';
import { useAuth } from '@/components/auth-provider';
import { useRouter } from 'next/navigation';
import { doc, setDoc, collection } from 'firebase/firestore';
import { db, handleFirestoreError, OperationType } from '@/lib/firebase';
import { Building2, Landmark, Shield } from 'lucide-react';
import { motion } from 'motion/react';

export default function OnboardingPage() {
  const { user, setOrganization } = useAuth();
  const router = useRouter();
  const [name, setName] = useState('');
  const [type, setType] = useState<'Bank' | 'Company'>('Company');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !name) return;
    setLoading(true);

    try {
      const orgRef = doc(collection(db, 'organizations'));
      const orgData = {
        name,
        type,
        subscriptionPlan: 'Starter',
        ownerId: user.uid,
        createdAt: new Date().toISOString(),
      };
      await setDoc(orgRef, orgData);

      const membershipRef = doc(collection(db, 'memberships'), `${user.uid}_${orgRef.id}`);
      await setDoc(membershipRef, {
        userId: user.uid,
        organizationId: orgRef.id,
        role: 'Owner',
        createdAt: new Date().toISOString(),
      });

      setOrganization({ id: orgRef.id, ...orgData }, 'Owner');
      router.push('/dashboard');
    } catch (error) {
      handleFirestoreError(error, OperationType.CREATE, 'organizations');
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center justify-center p-6 transition-colors duration-200">
      <div className="w-full max-w-md">
        <div className="flex justify-center mb-8">
          <div className="w-16 h-16 bg-indigo-100 dark:bg-indigo-900/50 rounded-2xl flex items-center justify-center">
            <Shield className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
          </div>
        </div>
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-8 transition-colors duration-200"
        >
          <h1 className="text-2xl font-bold text-center mb-2 text-slate-900 dark:text-white">Create Workspace</h1>
          <p className="text-slate-500 dark:text-slate-400 text-center mb-8">Set up your organization to start assessing your security posture.</p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Organization Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500"
                placeholder="Acme Corp"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">Organization Type</label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setType('Company')}
                  className={`p-4 border rounded-xl flex flex-col items-center gap-2 transition-colors ${
                    type === 'Company' ? 'border-indigo-600 dark:border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-400' : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 text-slate-900 dark:text-white'
                  }`}
                >
                  <Building2 className="w-6 h-6" />
                  <span className="font-medium">Company</span>
                </button>
                <button
                  type="button"
                  onClick={() => setType('Bank')}
                  className={`p-4 border rounded-xl flex flex-col items-center gap-2 transition-colors ${
                    type === 'Bank' ? 'border-indigo-600 dark:border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-400' : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 text-slate-900 dark:text-white'
                  }`}
                >
                  <Landmark className="w-6 h-6" />
                  <span className="font-medium">Bank</span>
                </button>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                {type === 'Bank' ? 'Stricter compliance profile, regulatory controls, and higher evidence expectations.' : 'General business profile, practical cyber hygiene, and fast wins.'}
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || !name}
              className="w-full bg-indigo-600 dark:bg-indigo-500 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Creating...' : 'Create Workspace'}
            </button>
          </form>
        </motion.div>
      </div>
    </div>
  );
}
