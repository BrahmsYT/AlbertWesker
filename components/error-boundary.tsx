'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      let errorDetails = null;
      try {
        if (this.state.error?.message.includes('FirestoreErrorInfo')) {
          errorDetails = JSON.parse(this.state.error.message);
        } else if (this.state.error?.message.startsWith('{')) {
          errorDetails = JSON.parse(this.state.error.message);
        }
      } catch (e) {
        // Not a JSON error
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-950 p-4 transition-colors duration-200">
          <div className="max-w-md w-full bg-white dark:bg-slate-900 rounded-xl shadow-lg p-6 border border-slate-200 dark:border-slate-800">
            <h2 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">Something went wrong</h2>
            <div className="bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300 p-4 rounded-lg text-sm mb-4 overflow-auto max-h-64 border border-red-100 dark:border-red-900/30">
              {errorDetails ? (
                <div>
                  <p className="font-semibold">Operation: {errorDetails.operationType}</p>
                  <p className="font-semibold">Path: {errorDetails.path}</p>
                  <p className="mt-2 text-xs font-mono whitespace-pre-wrap">{errorDetails.error}</p>
                </div>
              ) : (
                <p className="font-mono whitespace-pre-wrap">{this.state.error?.message}</p>
              )}
            </div>
            <button
              className="w-full bg-indigo-600 dark:bg-indigo-500 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors"
              onClick={() => window.location.reload()}
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
