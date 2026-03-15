'use client';

import { useAuth } from '@/components/auth-provider';
import { DashboardLayout } from '@/components/dashboard-layout';
import { db, handleFirestoreError, OperationType } from '@/lib/firebase';
import { doc, getDoc, updateDoc, collection, addDoc, serverTimestamp, setDoc } from 'firebase/firestore';
import { useEffect, useState, use } from 'react';
import { AlertTriangle, ShieldCheck, ListTodo, Bot, Send, Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import { GoogleGenAI } from '@google/genai';

export default function FindingDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const { organization, user } = useAuth();
  const router = useRouter();
  const [finding, setFinding] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState('');
  const [actionTitle, setActionTitle] = useState('');
  const [creatingAction, setCreatingAction] = useState(false);

  useEffect(() => {
    if (!organization) return;

    const fetchFinding = async () => {
      try {
        const docRef = doc(db, 'findings', resolvedParams.id);
        const docSnap = await getDoc(docRef);
        
        if (docSnap.exists() && docSnap.data().organizationId === organization.id) {
          setFinding({ id: docSnap.id, ...docSnap.data() });
        } else {
          router.push('/findings');
        }
      } catch (error) {
        handleFirestoreError(error, OperationType.GET, 'findings');
      } finally {
        setLoading(false);
      }
    };

    fetchFinding();
  }, [organization, resolvedParams.id, router]);

  const handleGenerateRemediation = async () => {
    if (!finding || !organization) return;
    setAiLoading(true);

    try {
      const ai = new GoogleGenAI({ apiKey: process.env.NEXT_PUBLIC_GEMINI_API_KEY });
      
      const systemInstruction = `You are CyberGap AI, an expert Cybersecurity and GRC co-pilot.
You are assisting an organization of type: ${organization.type}.

If the organization is a 'Bank':
- Emphasize strict regulatory compliance, board reporting, privileged access management, and continuous monitoring.
- Recommend formal governance structures and rigorous evidence collection.

If the organization is a 'Company':
- Emphasize practical cyber hygiene, fast wins, and budget-aware recommendations.
- Focus on foundational controls (MFA, backups, patching, endpoint protection).

Your capabilities:
- Explain security findings in both technical and business-friendly language.
- Map gaps to frameworks (ISO 27001, NIST CSF, CIS Controls).
- Generate prioritized 30/60/90-day remediation roadmaps.
- Draft executive summaries.

Always be professional, concise, and structure your responses with clear headings or bullet points.`;

      const chat = ai.chats.create({
        model: 'gemini-3.1-pro-preview',
        config: {
          systemInstruction,
          temperature: 0.7,
        }
      });

      const message = `Generate a step-by-step remediation plan for the following security finding.
Title: ${finding.title}
Description: ${finding.description}
Domain: ${finding.domain}
Severity: ${finding.severity}
Frameworks: ${finding.frameworkMapping.join(', ')}

Provide actionable steps, estimated effort, and specific controls to implement.`;

      const response = await chat.sendMessage({ message });
      const responseText = response.text || '';
      setAiResponse(responseText);

      // Save to finding
      const findingRef = doc(db, 'findings', finding.id);
      await updateDoc(findingRef, {
        remediationGuidance: responseText,
        updatedAt: new Date().toISOString()
      });
      
      setFinding(prev => ({ ...prev, remediationGuidance: responseText }));
    } catch (error) {
      console.error('AI Error:', error);
    } finally {
      setAiLoading(false);
    }
  };

  const handleCreateAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionTitle.trim() || !organization || !user) return;
    setCreatingAction(true);

    try {
      const actionRef = doc(collection(db, 'actions'));
      await setDoc(actionRef, {
        organizationId: organization.id,
        findingId: finding.id,
        title: actionTitle,
        description: `Remediate finding: ${finding.title}`,
        owner: user.displayName || user.email,
        dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days from now
        status: 'open',
        createdAt: new Date().toISOString()
      });

      // Update finding status
      const findingRef = doc(db, 'findings', finding.id);
      await updateDoc(findingRef, {
        status: 'in_progress',
        updatedAt: new Date().toISOString()
      });

      setFinding(prev => ({ ...prev, status: 'in_progress' }));
      setActionTitle('');
      alert('Remediation action created successfully!');
    } catch (error) {
      handleFirestoreError(error, OperationType.CREATE, 'actions');
    } finally {
      setCreatingAction(false);
    }
  };

  if (!organization || loading) return <DashboardLayout><div className="p-8">Loading...</div></DashboardLayout>;
  if (!finding) return <DashboardLayout><div className="p-8">Finding not found.</div></DashboardLayout>;

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <Link href="/findings" className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white mb-6 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Findings
        </Link>

        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden mb-8 transition-colors duration-200">
          <div className="p-6 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-3 mb-4">
              <span className={`px-3 py-1 text-xs font-bold uppercase tracking-wider rounded-full border ${
                finding.severity === 'Critical' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800' :
                finding.severity === 'High' ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 border-orange-200 dark:border-orange-800' :
                finding.severity === 'Medium' ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800' :
                'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800'
              }`}>
                {finding.severity}
              </span>
              <span className="text-sm font-medium text-slate-500 dark:text-slate-400">{finding.domain}</span>
              <span className="text-sm font-medium text-slate-500 dark:text-slate-400 capitalize px-2 py-0.5 bg-slate-100 dark:bg-slate-800 rounded">
                {finding.status.replace('_', ' ')}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">{finding.title}</h1>
            <p className="text-slate-600 dark:text-slate-300 whitespace-pre-wrap">{finding.description}</p>
          </div>
          
          <div className="bg-slate-50 dark:bg-slate-900/50 p-6 flex flex-col sm:flex-row gap-6">
            <div className="flex-1">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> Framework Mapping
              </h3>
              <div className="flex flex-wrap gap-2">
                {finding.frameworkMapping.map((f: string) => (
                  <span key={f} className="px-2.5 py-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs rounded-md font-medium">
                    {f}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" /> Source
              </h3>
              <span className="px-2.5 py-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs rounded-md font-medium">
                {finding.source}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden transition-colors duration-200">
              <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Bot className="w-5 h-5 text-indigo-600 dark:text-indigo-400" /> AI Remediation Guidance
                </h2>
                {(!finding.remediationGuidance || finding.remediationGuidance === 'To be generated by AI') && (
                  <button
                    onClick={handleGenerateRemediation}
                    disabled={aiLoading}
                    className="px-4 py-2 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 rounded-lg text-sm font-medium hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors flex items-center gap-2 disabled:opacity-50"
                  >
                    {aiLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Bot className="w-4 h-4" />}
                    Generate Plan
                  </button>
                )}
              </div>
              <div className="p-6">
                {finding.remediationGuidance && finding.remediationGuidance !== 'To be generated by AI' ? (
                  <div className="prose prose-sm prose-indigo dark:prose-invert max-w-none">
                    <ReactMarkdown>{finding.remediationGuidance}</ReactMarkdown>
                  </div>
                ) : aiLoading ? (
                  <div className="flex items-center justify-center py-12 text-indigo-600 dark:text-indigo-400">
                    <Loader2 className="w-8 h-8 animate-spin" />
                    <span className="ml-3 font-medium">Analyzing finding and generating roadmap...</span>
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-500 dark:text-slate-400">
                    <p>No remediation guidance generated yet.</p>
                    <p className="text-sm mt-2">Click &quot;Generate Plan&quot; to have CyberGap AI analyze this finding and create a step-by-step roadmap.</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-8">
            <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden transition-colors duration-200">
              <div className="p-6 border-b border-slate-200 dark:border-slate-800">
                <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <ListTodo className="w-5 h-5 text-emerald-600 dark:text-emerald-400" /> Create Action
                </h2>
              </div>
              <div className="p-6">
                <form onSubmit={handleCreateAction} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Action Title</label>
                    <input
                      type="text"
                      required
                      value={actionTitle}
                      onChange={(e) => setActionTitle(e.target.value)}
                      placeholder="e.g., Implement MFA for VPN"
                      className="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm placeholder:text-slate-400 dark:placeholder:text-slate-500"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={creatingAction || !actionTitle.trim()}
                    className="w-full px-4 py-2 bg-emerald-600 dark:bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 dark:hover:bg-emerald-600 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {creatingAction ? 'Creating...' : 'Create Action Task'}
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
