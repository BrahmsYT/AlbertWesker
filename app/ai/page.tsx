'use client';

import { useAuth } from '@/components/auth-provider';
import { DashboardLayout } from '@/components/dashboard-layout';
import { useState, useRef, useEffect } from 'react';
import { Bot, Send, User, Loader2, Sparkles } from 'lucide-react';
import { motion } from 'motion/react';
import ReactMarkdown from 'react-markdown';
import { GoogleGenAI } from '@google/genai';

export default function AIAssistantPage() {
  const { organization } = useAuth();
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant', content: string }[]>([
    { role: 'assistant', content: 'Hello! I am your CyberGap AI Assistant. I can help explain findings, map controls to frameworks, generate remediation roadmaps, or answer questions about your security posture. How can I assist you today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading || !organization) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

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

Always be professional, concise, and structure your responses with clear headings or bullet points.
Do not hallucinate specific findings if none are provided in the prompt context, but you can provide general best practices.`;

      const chat = ai.chats.create({
        model: 'gemini-3.1-pro-preview',
        config: {
          systemInstruction,
          temperature: 0.7,
        }
      });

      // Replay history
      for (const msg of messages) {
        if (msg.role === 'user') {
          await chat.sendMessage({ message: msg.content });
        }
      }

      const response = await chat.sendMessage({ message: userMessage });

      setMessages(prev => [...prev, { role: 'assistant', content: response.text || '' }]);
    } catch (error) {
      console.error('AI Error:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error processing your request. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const suggestedPrompts = [
    "What are the most critical gaps in our current posture?",
    "Generate a 30-day remediation roadmap for our open findings.",
    "Explain the difference between ISO 27001 and NIST CSF.",
    "Draft an executive summary of our latest assessment."
  ];

  if (!organization) return null;

  return (
    <DashboardLayout>
      <div className="h-[calc(100vh-8rem)] flex flex-col max-w-5xl mx-auto bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden transition-colors duration-200">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/50 rounded-xl flex items-center justify-center">
            <Bot className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h2 className="font-bold text-slate-900 dark:text-white">CyberGap AI Assistant</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Context-aware GRC & Security Co-pilot</p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50 dark:bg-slate-950/50">
          {messages.map((msg, idx) => (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              key={idx} 
              className={`flex gap-4 max-w-[85%] ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
            >
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                msg.role === 'user' ? 'bg-slate-200 dark:bg-slate-700' : 'bg-indigo-600 dark:bg-indigo-500'
              }`}>
                {msg.role === 'user' ? <User className="w-5 h-5 text-slate-600 dark:text-slate-300" /> : <Sparkles className="w-4 h-4 text-white" />}
              </div>
              <div className={`p-4 rounded-2xl ${
                msg.role === 'user' 
                  ? 'bg-indigo-600 dark:bg-indigo-500 text-white rounded-tr-sm' 
                  : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 rounded-tl-sm shadow-sm'
              }`}>
                {msg.role === 'user' ? (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <div className="prose prose-sm prose-indigo dark:prose-invert max-w-none">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
          {loading && (
            <div className="flex gap-4 max-w-[85%]">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-600 dark:bg-indigo-500 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-tl-sm shadow-sm flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-indigo-600 dark:text-indigo-400 animate-spin" />
                <span className="text-sm text-slate-500 dark:text-slate-400">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          {messages.length === 1 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {suggestedPrompts.map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => setInput(prompt)}
                  className="text-xs px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-full transition-colors border border-slate-200 dark:border-slate-700"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your security posture, roadmaps, or controls..."
              className="flex-1 px-4 py-3 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="px-4 py-3 bg-indigo-600 dark:bg-indigo-500 text-white rounded-xl hover:bg-indigo-700 dark:hover:bg-indigo-600 disabled:opacity-50 transition-colors flex items-center justify-center"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </DashboardLayout>
  );
}
