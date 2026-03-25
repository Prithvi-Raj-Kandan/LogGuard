import { LogLine } from '../types';
import { AlertTriangle, Shield, AlertCircle, XCircle } from 'lucide-react';

interface LogViewerProps {
  logs: LogLine[];
}

export function LogViewer({ logs }: LogViewerProps) {
  const getRiskIcon = (riskLevel?: string) => {
    switch (riskLevel) {
      case 'critical':
        return <XCircle className="w-4 h-4 text-[#ef4444]" />;
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-[#f97316]" />;
      case 'medium':
        return <AlertCircle className="w-4 h-4 text-[#fbbf24]" />;
      case 'low':
        return <Shield className="w-4 h-4 text-[#3b82f6]" />;
      default:
        return null;
    }
  };

  const getRiskColor = (riskLevel?: string) => {
    switch (riskLevel) {
      case 'critical':
        return 'bg-[#ef4444]/10 border-l-[#ef4444]';
      case 'high':
        return 'bg-[#f97316]/10 border-l-[#f97316]';
      case 'medium':
        return 'bg-[#fbbf24]/10 border-l-[#fbbf24]';
      case 'low':
        return 'bg-[#3b82f6]/10 border-l-[#3b82f6]';
      default:
        return 'bg-transparent border-l-transparent';
    }
  };

  return (
    <div className="bg-[#0d0d0d] rounded-lg border border-[#2a2a2a] overflow-hidden">
      <div className="bg-[#1a1a1a] px-4 py-3 border-b border-[#2a2a2a]">
        <h3 className="text-[#e0e0e0] font-mono flex items-center gap-2">
          <Shield className="w-4 h-4" />
          Log Contents
        </h3>
      </div>
      
      <div className="max-h-[500px] overflow-y-auto">
        <div className="font-mono text-sm">
          {logs.map((log) => (
            <div
              key={log.lineNumber}
              className={`
                flex items-start gap-3 px-4 py-2 border-l-2 hover:bg-[#1a1a1a]/50 transition-colors
                ${getRiskColor(log.riskLevel)}
                ${log.isSensitive ? 'bg-opacity-20' : ''}
              `}
            >
              {/* Line Number */}
              <span className="text-[#666] select-none min-w-[3rem] text-right">
                {log.lineNumber}
              </span>

              {/* Risk Marker */}
              <span className="min-w-[1.5rem] flex items-center justify-center">
                {getRiskIcon(log.riskLevel)}
              </span>

              {/* Log Content */}
              <span className={`flex-1 ${log.isSensitive ? 'text-[#fbbf24]' : 'text-[#a0a0a0]'}`}>
                {log.content}
              </span>

              {/* Sensitive Badge */}
              {log.isSensitive && (
                <span className="text-xs px-2 py-1 bg-[#fbbf24]/20 text-[#fbbf24] rounded">
                  SENSITIVE
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
