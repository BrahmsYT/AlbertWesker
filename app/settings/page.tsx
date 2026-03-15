'use client';

import { useAuth } from '@/components/auth-provider';
import { DashboardLayout } from '@/components/dashboard-layout';
import { db } from '@/lib/firebase';
import { doc, setDoc } from 'firebase/firestore';
import { Lock, Shield, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { useState } from 'react';

export default function SettingsPage() {
  const { organization } = useAuth();
  const [activeTab, setActiveTab] = useState<'general' | 'security' | 'members' | 'audit'>('general');
  const [saving, setSaving] = useState(false);
  const [orgName, setOrgName] = useState(organization?.name || '');

  const handleSaveOrgName = async () => {
    if (orgName === organization?.name || !orgName.trim()) return;
    setSaving(true);
    try {
      // Real Firestore update with rollback on error
      const orgRef = doc(db, 'organizations', organization.id);
      await setDoc(orgRef, { name: orgName, updatedAt: new Date().toISOString() }, { merge: true });
      // Success: silent completion, name is already updated in UI
      setSaving(false);
    } catch (error) {
      setSaving(false);
      // Rollback: revert input to last saved state
      setOrgName(organization?.name || '');
      console.error('Failed to update organization name:', error);
      // Show error message (could use toast instead of alert)
      alert(`Failed to save: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  if (!organization) return null;

  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Settings</h1>
          <p className="text-slate-500 dark:text-slate-400">Manage your organization and account preferences.</p>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-slate-200 dark:border-slate-800 mb-8 flex gap-8">
          <button
            onClick={() => setActiveTab('general')}
            className={`pb-4 px-1 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'general'
                ? 'border-indigo-600 dark:border-indigo-500 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            General
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`pb-4 px-1 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'security'
                ? 'border-indigo-600 dark:border-indigo-500 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Security
          </button>
          <button
            onClick={() => setActiveTab('members')}
            className={`pb-4 px-1 font-medium text-sm border-b-2 transition-colors disabled opacity-50 ${
              activeTab === 'members'
                ? 'border-indigo-600 dark:border-indigo-500 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
            disabled
            title="Coming soon"
          >
            Members
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`pb-4 px-1 font-medium text-sm border-b-2 transition-colors disabled opacity-50 ${
              activeTab === 'audit'
                ? 'border-indigo-600 dark:border-indigo-500 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
            disabled
            title="Coming soon"
          >
            Audit Log
          </button>
        </div>

        {/* General Tab */}
        {activeTab === 'general' && (
          <div className="space-y-8">
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                <Shield className="w-5 h-5 text-indigo-600 dark:text-indigo-400" /> Organization Profile
              </h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Organization Name
                  </label>
                  <input
                    type="text"
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    className="w-full px-4 py-3 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                  />
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Used in reports and compliance documents.</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Organization Type
                  </label>
                  <div className="px-4 py-3 border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white rounded-lg">
                    {organization.type}
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">This determines framework recommendations and compliance baselines.</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Subscription Plan
                  </label>
                  <div className="px-4 py-3 border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white rounded-lg flex items-center justify-between">
                    <span>{organization.subscriptionPlan}</span>
                    <span className="text-xs bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 px-2 py-1 rounded">Current</span>
                  </div>
                </div>

                <div className="pt-4 flex justify-end">
                  <button
                    onClick={handleSaveOrgName}
                    disabled={saving || orgName === organization?.name}
                    className="px-6 py-2 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors disabled:opacity-50 flex items-center gap-2"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                    Save Changes
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Security Tab */}
        {activeTab === 'security' && (
          <div className="space-y-8">
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                <Lock className="w-5 h-5 text-indigo-600 dark:text-indigo-400" /> Security Settings
              </h2>

              <div className="space-y-6">
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex gap-3">
                  <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                  <div>
                    <h3 className="font-medium text-blue-900 dark:text-blue-300">Advanced Security</h3>
                    <p className="text-sm text-blue-700 dark:text-blue-400 mt-1">Additional security settings (API keys, SSO, 2FA enforcement) coming soon in Professional plan.</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
                    <div>
                      <h3 className="font-medium text-slate-900 dark:text-white">Data Encryption</h3>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">All data encrypted in transit (TLS 1.3) and at rest (AES-256)</p>
                    </div>
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  </div>

                  <div className="flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
                    <div>
                      <h3 className="font-medium text-slate-900 dark:text-white">Tenant Isolation</h3>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Data strictly isolated by organization at database and API layer</p>
                    </div>
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  </div>

                  <div className="flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
                    <div>
                      <h3 className="font-medium text-slate-900 dark:text-white">Audit Logging</h3>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">All sensitive actions logged with user, timestamp, and outcome</p>
                    </div>
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Placeholder Tabs */}
        {(activeTab === 'members' || activeTab === 'audit') && (
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8 text-center">
            <AlertCircle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Coming Soon</h2>
            <p className="text-slate-600 dark:text-slate-400">This feature will be available in the next release.</p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
