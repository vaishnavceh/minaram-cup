import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error caught by ErrorBoundary:', error, errorInfo);
  }

  public handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#080808] text-white flex flex-col items-center justify-center p-6 text-center">
          <div className="w-16 h-16 rounded-full bg-brand-red/20 border border-brand-red flex items-center justify-center text-brand-red mb-4">
            <AlertTriangle className="w-8 h-8" />
          </div>
          <h1 className="font-display text-4xl text-white tracking-wider mb-2">
            EXPERIENCING A MATCH INTERRUPT
          </h1>
          <p className="text-neutral-400 text-sm max-w-md mb-6 font-mono">
            {this.state.error?.message || 'A render disturbance occurred while displaying tournament data.'}
          </p>
          <button
            onClick={this.handleReload}
            className="px-6 py-2.5 bg-brand-red hover:bg-brand-red-bright text-white font-display text-base tracking-wider rounded flex items-center space-x-2 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>RELOAD TOURNAMENT ARENA</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
