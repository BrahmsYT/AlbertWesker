'use client';

import { useAuth } from '@/components/auth-provider';
import { DashboardLayout } from '@/components/dashboard-layout';
import { useState } from 'react';
import { Search, ShieldAlert, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

export default function ScanPage() {
  const { organization } = useAuth();
  const router = useRouter();
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!domain || !organization) return;
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      // Call the new async scan API
      const response = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          organizationId: organization.id,
          domain,
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Scan failed');
      }

      const data = await response.json();
      setJobId(data.jobId);
      setResults({
        domain: data.domain,
        status: data.status,
        jobId: data.jobId,
        createdAt: data.createdAt,
      });

      // Start polling for job completion (max 5 minutes)
      let pollCount = 0;
      const maxPolls = 300; // 5 min @ 1 sec interval
      const pollInterval = setInterval(async () => {
        try {
          pollCount++;
          const statusRes = await fetch(`/api/scan?jobId=${data.jobId}`);
          if (!statusRes.ok) throw new Error('Status fetch failed');
          const statusData = await statusRes.json();

          setResults((prev) => ({
            ...prev,
            status: statusData.status,
            findings: statusData.findings || [],
            error: statusData.error,
          }));

          // Stop polling when job is done or failed
          if (['completed', 'failed', 'cancelled'].includes(statusData.status) || pollCount >= maxPolls) {
            clearInterval(pollInterval);
          }
        } catch (err) {
          console.error('Polling error:', err);
          // Continue polling on transient errors
        }
      }, 1000); // Poll every 1 second
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to run scan';
      setError(errorMsg);
      console.error('Scan Error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!organization) return null;

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">External Attack Surface Scan</h1>
          <p className="text-slate-500 dark:text-slate-400">Analyze your public-facing infrastructure for security gaps. Domain ownership verification required.</p>
        </div>

        {/* Scan Input Form */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-8 mb-8 transition-colors duration-200">
          <form onSubmit={handleScan} className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="w-5 h-5 text-slate-400 dark:text-slate-500 absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                required
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="e.g., example.com"
                className="w-full pl-12 pr-4 py-4 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-lg placeholder:text-slate-400 dark:placeholder:text-slate-500"
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !domain}
              className="px-8 py-4 bg-indigo-600 dark:bg-indigo-500 text-white rounded-xl font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 disabled:opacity-50 transition-colors flex items-center justify-center gap-2 text-lg"
            >
              {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : 'Run Scan'}
            </button>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-6 mb-8 flex gap-4">
            <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-red-900 dark:text-red-300">Scan Failed</h3>
              <p className="text-red-700 dark:text-red-400 mt-1 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Job Created - Polling Message */}
        {results && results.status === 'queued' && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden transition-colors duration-200">
            <div className="p-6 border-b border-blue-200 dark:border-blue-800 flex items-center gap-3">
              <Loader2 className="w-6 h-6 text-blue-600 dark:text-blue-400 animate-spin" />
              <h2 className="text-lg font-bold text-blue-900 dark:text-blue-300">Scan in Progress</h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-blue-700 dark:text-blue-400 font-medium">Job ID</p>
                  <p className="text-slate-900 dark:text-white font-mono text-sm mt-1">{results.jobId}</p>
                </div>
                <div>
                  <p className="text-sm text-blue-700 dark:text-blue-400 font-medium">Domain</p>
                  <p className="text-slate-900 dark:text-white mt-1">{results.domain}</p>
                </div>
                <div>
                  <p className="text-sm text-blue-700 dark:text-blue-400 font-medium">Status</p>
                  <p className="text-slate-900 dark:text-white capitalize mt-1">
                    <span className="inline-flex items-center gap-2">
                      <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                      Queued - will begin shortly
                    </span>
                  </p>
                </div>
                <p className="text-xs text-blue-600 dark:text-blue-400 mt-4">
                  💡 Tip: Real scans require domain ownership verification via DNS TXT record. This step is coming in the next release.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Info Box */}
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-2xl p-6 mt-8">
          <div className="flex gap-4">
            <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-amber-900 dark:text-amber-300">How External Scanning Works</h3>
              <ul className="text-amber-800 dark:text-amber-400 text-sm mt-2 space-y-1">
                <li>• Enter your domain (e.g., example.com)</li>
                <li>• System analyzes DNS, TLS, HTTP headers, mail security, and public services</li>
                <li>• Findings are mapped to ISO 27001, NIST, CIS Controls, and Bank Regulatory standards</li>
                <li>• Results are saved and linked to your security assessments</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
