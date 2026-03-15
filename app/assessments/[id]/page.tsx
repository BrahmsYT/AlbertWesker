'use client';

import { useAuth } from '@/components/auth-provider';
import { DashboardLayout } from '@/components/dashboard-layout';
import { db, handleFirestoreError, OperationType } from '@/lib/firebase';
import { doc, getDoc, collection, query, where, getDocs, writeBatch } from 'firebase/firestore';
import { useEffect, useState, use } from 'react';
import { QUESTIONS, Question } from '@/lib/questions';
import { CheckCircle2, AlertCircle, Save, ArrowRight, Activity } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function AssessmentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const { organization } = useAuth();
  const router = useRouter();
  const [assessment, setAssessment] = useState<any>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, { value: string, notes: string }>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!organization) return;

    const fetchAssessmentData = async () => {
      try {
        const docRef = doc(db, 'assessments', resolvedParams.id);
        const docSnap = await getDoc(docRef);
        
        if (docSnap.exists() && docSnap.data().organizationId === organization.id) {
          const data = docSnap.data();
          setAssessment({ id: docSnap.id, ...data });

          // Filter questions based on org type and frameworks
          const filteredQuestions = QUESTIONS.filter(q => {
            const matchesType = q.type === 'Both' || q.type === organization.type;
            const matchesFramework = q.frameworks.some(f => data.frameworks.includes(f));
            return matchesType && matchesFramework;
          });
          setQuestions(filteredQuestions);

          // Fetch existing answers
          const answersQ = query(
            collection(db, 'answers'),
            where('assessmentId', '==', resolvedParams.id)
          );
          const answersSnap = await getDocs(answersQ);
          const existingAnswers: Record<string, any> = {};
          answersSnap.forEach(a => {
            const ansData = a.data();
            existingAnswers[ansData.questionId] = {
              value: ansData.value,
              notes: ansData.notes || ''
            };
          });

          // Initialize missing answers
          filteredQuestions.forEach(q => {
            if (!existingAnswers[q.id]) {
              existingAnswers[q.id] = { value: 'Unanswered', notes: '' };
            }
          });

          setAnswers(existingAnswers);
        } else {
          router.push('/assessments');
        }
      } catch (error) {
        handleFirestoreError(error, OperationType.GET, 'assessments');
      } finally {
        setLoading(false);
      }
    };

    fetchAssessmentData();
  }, [organization, resolvedParams.id, router]);

  const handleAnswerChange = (questionId: string, value: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: { ...prev[questionId], value }
    }));
  };

  const handleNotesChange = (questionId: string, notes: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: { ...prev[questionId], notes }
    }));
  };

  const handleSave = async (complete: boolean = false) => {
    if (!organization || !assessment) return;
    setSaving(true);

    try {
      const batch = writeBatch(db);
      
      // Calculate score
      let totalScore = 0;
      let answeredCount = 0;
      
      Object.entries(answers).forEach(([qId, ans]) => {
        const q = questions.find(qu => qu.id === qId);
        if (!q) return;

        const answerRef = doc(collection(db, 'answers'), `${assessment.id}_${qId}`);
        batch.set(answerRef, {
          assessmentId: assessment.id,
          organizationId: organization.id,
          questionId: qId,
          domain: q.domain,
          value: ans.value,
          notes: ans.notes,
          updatedAt: new Date().toISOString()
        });

        if (ans.value !== 'Unanswered' && ans.value !== 'N/A') {
          answeredCount++;
          if (ans.value === 'Yes') totalScore += 1;
          if (ans.value === 'Partial') totalScore += 0.5;
        }
      });

      const maturityScore = answeredCount > 0 ? Math.round((totalScore / answeredCount) * 100) : 0;
      const newStatus = complete ? 'completed' : 'in_progress';

      const assessmentRef = doc(db, 'assessments', assessment.id);
      batch.update(assessmentRef, {
        status: newStatus,
        maturityScore,
        updatedAt: new Date().toISOString()
      });

      await batch.commit();
      setAssessment(prev => ({ ...prev, status: newStatus, maturityScore }));
      
      if (complete) {
        // Generate findings based on 'No' or 'Partial' answers
        await generateFindings(answers, questions);
        router.push(`/assessments/${assessment.id}/results`);
      }
    } catch (error) {
      handleFirestoreError(error, OperationType.UPDATE, 'answers');
    } finally {
      setSaving(false);
    }
  };

  const generateFindings = async (currentAnswers: Record<string, any>, currentQuestions: Question[]) => {
    const batch = writeBatch(db);
    
    currentQuestions.forEach(q => {
      const ans = currentAnswers[q.id];
      if (ans.value === 'No' || ans.value === 'Partial') {
        const findingRef = doc(collection(db, 'findings'));
        batch.set(findingRef, {
          organizationId: organization.id,
          assessmentId: assessment.id,
          title: `Gap in ${q.domain}: ${q.text.split('?')[0]}`,
          description: `The organization answered '${ans.value}' to the control: "${q.text}".\nNotes: ${ans.notes || 'None provided.'}`,
          source: 'Assessment',
          severity: ans.value === 'No' ? 'High' : 'Medium',
          domain: q.domain,
          frameworkMapping: q.frameworks,
          remediationGuidance: 'To be generated by AI',
          status: 'open',
          createdAt: new Date().toISOString()
        });
      }
    });

    await batch.commit();
  };

  if (!organization || loading) return <DashboardLayout><div className="p-8">Loading...</div></DashboardLayout>;

  // Group questions by domain
  const groupedQuestions = questions.reduce((acc, q) => {
    if (!acc[q.domain]) acc[q.domain] = [];
    acc[q.domain].push(q);
    return acc;
  }, {} as Record<string, Question[]>);

  const progress = Math.round((Object.values(answers).filter(a => a.value !== 'Unanswered').length / questions.length) * 100) || 0;

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-1 rounded">
                {assessment.status.replace('_', ' ')}
              </span>
              <span className="text-sm text-slate-500 dark:text-slate-400">{assessment.frameworks.join(', ')}</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{assessment.name}</h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => handleSave(false)}
              disabled={saving || assessment.status === 'completed'}
              className="px-4 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 rounded-lg font-medium hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              <Save className="w-4 h-4" /> Save Draft
            </button>
            <button
              onClick={() => handleSave(true)}
              disabled={saving || assessment.status === 'completed' || progress < 100}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              <CheckCircle2 className="w-4 h-4" /> Complete Assessment
            </button>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 mb-8 transition-colors duration-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Completion Progress</span>
            <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">{progress}%</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2.5">
            <div className="bg-indigo-600 dark:bg-indigo-500 h-2.5 rounded-full transition-all duration-500" style={{ width: `${progress}%` }}></div>
          </div>
          {progress < 100 && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5" /> Answer all questions to complete the assessment.
            </p>
          )}
        </div>

        <div className="space-y-8">
          {Object.entries(groupedQuestions).map(([domain, domainQuestions]) => (
            <div key={domain} className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden transition-colors duration-200">
              <div className="bg-slate-50 dark:bg-slate-900/50 px-6 py-4 border-b border-slate-200 dark:border-slate-800">
                <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Activity className="w-5 h-5 text-indigo-500 dark:text-indigo-400" />
                  {domain}
                </h2>
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {domainQuestions.map((q, index) => (
                  <div key={q.id} className="p-6">
                    <div className="flex flex-col md:flex-row gap-6">
                      <div className="flex-1">
                        <div className="flex items-start gap-3">
                          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center text-xs font-bold">
                            {index + 1}
                          </span>
                          <div>
                            <p className="text-slate-900 dark:text-white font-medium mb-2">{q.text}</p>
                            <div className="flex flex-wrap gap-2 mb-4">
                              {['Yes', 'Partial', 'No', 'N/A'].map(val => (
                                <button
                                  key={val}
                                  onClick={() => handleAnswerChange(q.id, val)}
                                  disabled={assessment.status === 'completed'}
                                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${
                                    answers[q.id]?.value === val
                                      ? val === 'Yes' ? 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400'
                                      : val === 'No' ? 'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400'
                                      : val === 'Partial' ? 'bg-amber-50 dark:bg-amber-900/30 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400'
                                      : 'bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300'
                                      : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-600'
                                  }`}
                                >
                                  {val}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="w-full md:w-64 flex-shrink-0">
                        <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Notes / Evidence Link</label>
                        <textarea
                          value={answers[q.id]?.notes || ''}
                          onChange={(e) => handleNotesChange(q.id, e.target.value)}
                          disabled={assessment.status === 'completed'}
                          placeholder="Add context or links to policies..."
                          className="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none resize-none h-24 placeholder:text-slate-400 dark:placeholder:text-slate-500"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
