'use client';

import { useAuth } from '@/components/auth-provider';
import { DashboardLayout } from '@/components/dashboard-layout';
import { db, handleFirestoreError, OperationType } from '@/lib/firebase';
import { collection, query, where, getDocs, orderBy, addDoc } from 'firebase/firestore';
import { useEffect, useState } from 'react';
import { ListTodo, Search, Plus, CheckCircle2, Clock, AlertCircle, X, Loader2 } from 'lucide-react';
import { format } from 'date-fns';

export default function ActionsPage() {
  const { organization, user } = useAuth();
  const [actions, setActions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');

  useEffect(() => {
    const fetchActions = async () => {
      if (!organization) return;
      try {
        const q = query(
          collection(db, 'actions'),
          where('organizationId', '==', organization.id),
          orderBy('createdAt', 'desc')
        );
        const snap = await getDocs(q);
        const data = snap.docs.map(doc => ({ id: doc.id, ...doc.data() }));
        setActions(data);
      } catch (error) {
        handleFirestoreError(error, OperationType.LIST, 'actions');
      } finally {
        setLoading(false);
      }
    };

    fetchActions();
  }, [organization]);

  const handleCreateAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!organization || !user) return;
    setCreating(true);

    try {
      await addDoc(collection(db, 'actions'), {
        organizationId: organization.id,
        findingId: 'manual', // Indicates it was created manually, not from a specific finding
        title,
        description,
        owner: user.displayName || user.email,
        dueDate: dueDate ? new Date(dueDate).toISOString() : null,
        status: 'open',
        createdAt: new Date().toISOString()
      });

      setIsModalOpen(false);
      setTitle('');
      setDescription('');
      setDueDate('');
      
      // Re-fetch actions
      const q = query(
        collection(db, 'actions'),
        where('organizationId', '==', organization.id),
        orderBy('createdAt', 'desc')
      );
      const snap = await getDocs(q);
      const data = snap.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setActions(data);
    } catch (error) {
      handleFirestoreError(error, OperationType.CREATE, 'actions');
    } finally {
      setCreating(false);
    }
  };

  if (!organization) return null;

  return (
    <DashboardLayout>
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Remediation Actions</h1>
          <p className="text-slate-500 dark:text-slate-400">Track tasks to mitigate findings and close gaps.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-indigo-600 dark:bg-indigo-500 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          New Action
        </button>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden transition-colors duration-200">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center">
          <div className="relative w-full max-w-md">
            <Search className="w-5 h-5 text-slate-400 dark:text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input 
              type="text" 
              placeholder="Search actions..." 
              className="w-full pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500"
            />
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-500 dark:text-slate-400">Loading actions...</div>
        ) : actions.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center">
            <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
              <ListTodo className="w-8 h-8 text-slate-400 dark:text-slate-500" />
            </div>
            <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">No remediation actions</h3>
            <p className="text-slate-500 dark:text-slate-400 mb-6 max-w-sm">Create actions from findings to build your remediation roadmap.</p>
            <button 
              onClick={() => setIsModalOpen(true)}
              className="bg-indigo-600 dark:bg-indigo-500 text-white px-6 py-2 rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors"
            >
              New Action
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-800 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold">
                  <th className="p-4">Action Title</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Owner</th>
                  <th className="p-4">Due Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {actions.map((action) => (
                  <tr key={action.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="p-4">
                      <div className="font-medium text-slate-900 dark:text-white">{action.title}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate max-w-xs">{action.description}</div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-1.5">
                        {action.status === 'done' ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        ) : action.status === 'blocked' ? (
                          <AlertCircle className="w-4 h-4 text-red-500" />
                        ) : (
                          <Clock className="w-4 h-4 text-amber-500" />
                        )}
                        <span className="text-sm font-medium capitalize text-slate-700 dark:text-slate-300">
                          {action.status.replace('_', ' ')}
                        </span>
                      </div>
                    </td>
                    <td className="p-4 text-sm text-slate-600 dark:text-slate-300">{action.owner || 'Unassigned'}</td>
                    <td className="p-4 text-sm text-slate-500 dark:text-slate-400">
                      {action.dueDate ? format(new Date(action.dueDate), 'MMM d, yyyy') : 'No date'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Action Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-lg overflow-hidden transition-colors duration-200">
            <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">Create Remediation Action</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateAction} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Action Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Update Firewall Rules"
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm placeholder:text-slate-400 dark:placeholder:text-slate-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Description</label>
                <textarea
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  placeholder="Describe the steps required to complete this action..."
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm resize-none placeholder:text-slate-400 dark:placeholder:text-slate-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Due Date</label>
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                />
              </div>
              <div className="pt-4 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !title || !description}
                  className="px-4 py-2 bg-indigo-600 dark:bg-indigo-500 text-white font-medium rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors disabled:opacity-50 flex items-center gap-2 text-sm"
                >
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create Action'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
