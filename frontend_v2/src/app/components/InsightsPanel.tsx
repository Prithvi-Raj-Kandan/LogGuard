import { AnalysisReport } from '../types';
import { Brain, AlertTriangle, TrendingUp, XCircle, AlertCircle, Shield } from 'lucide-react';

interface InsightsPanelProps {
  report: AnalysisReport;
}

export function InsightsPanel({ report }: InsightsPanelProps) {
  const totalRisks = 
    report.riskBreakdown.critical +
    report.riskBreakdown.high +
    report.riskBreakdown.medium +
    report.riskBreakdown.low;

  return (
    <div className="space-y-4">
      {/* AI Summary */}
      <div className="bg-[#0d0d0d] rounded-lg border border-[#2a2a2a] overflow-hidden">
        <div className="bg-[#1a1a1a] px-4 py-3 border-b border-[#2a2a2a]">
          <h3 className="text-[#e0e0e0] font-mono flex items-center gap-2">
            <Brain className="w-4 h-4 text-[#8b5cf6]" />
            AI Summary
          </h3>
        </div>
        <div className="p-4 max-h-[260px] overflow-y-auto">
          <p className="text-[#a0a0a0] font-mono text-sm whitespace-pre-line leading-relaxed">
            {report.aiSummary}
          </p>
        </div>
      </div>

      {/* Risk Breakdown */}
      <div className="bg-[#0d0d0d] rounded-lg border border-[#2a2a2a] overflow-hidden">
        <div className="bg-[#1a1a1a] px-4 py-3 border-b border-[#2a2a2a]">
          <h3 className="text-[#e0e0e0] font-mono flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[#8b5cf6]" />
            Risk Breakdown
          </h3>
        </div>
        <div className="p-4 space-y-3">
          <RiskItem
            label="Critical"
            count={report.riskBreakdown.critical}
            total={totalRisks}
            color="#ef4444"
            icon={<XCircle className="w-4 h-4" />}
          />
          <RiskItem
            label="High"
            count={report.riskBreakdown.high}
            total={totalRisks}
            color="#f97316"
            icon={<AlertTriangle className="w-4 h-4" />}
          />
          <RiskItem
            label="Medium"
            count={report.riskBreakdown.medium}
            total={totalRisks}
            color="#fbbf24"
            icon={<AlertCircle className="w-4 h-4" />}
          />
          <RiskItem
            label="Low"
            count={report.riskBreakdown.low}
            total={totalRisks}
            color="#3b82f6"
            icon={<Shield className="w-4 h-4" />}
          />
        </div>
      </div>

      {/* Security Warnings */}
      <div className="bg-[#0d0d0d] rounded-lg border border-[#2a2a2a] overflow-hidden">
        <div className="bg-[#1a1a1a] px-4 py-3 border-b border-[#2a2a2a]">
          <h3 className="text-[#e0e0e0] font-mono flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-[#f97316]" />
            Security Warnings ({report.warnings.length})
          </h3>
        </div>
        <div className="p-4 space-y-3 max-h-[400px] overflow-y-auto">
          {report.warnings.map((warning) => (
            <div
              key={warning.id}
              className="p-3 bg-[#1a1a1a] rounded border-l-2 border-l-[var(--severity-color)]"
              style={{
                '--severity-color': getSeverityColor(warning.severity),
              } as React.CSSProperties}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="text-[#e0e0e0] font-mono text-sm">
                  {warning.type}
                </span>
                <span
                  className="text-xs px-2 py-1 rounded font-mono"
                  style={{
                    backgroundColor: `${getSeverityColor(warning.severity)}20`,
                    color: getSeverityColor(warning.severity),
                  }}
                >
                  {warning.severity.toUpperCase()}
                </span>
              </div>
              <p className="text-[#a0a0a0] font-mono text-sm mb-2">
                {warning.message}
              </p>
              {warning.redactionHint && (
                <p className="text-xs text-[#9ca3af] font-mono mb-2">
                  Redaction: {warning.redactionHint}
                </p>
              )}
              <div className="flex items-center gap-2 text-xs text-[#666] font-mono">
                <span>Lines:</span>
                {warning.lineNumbers.map((lineNum, idx) => (
                  <span key={lineNum}>
                    {lineNum}
                    {idx < warning.lineNumbers.length - 1 ? ',' : ''}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

interface RiskItemProps {
  label: string;
  count: number;
  total: number;
  color: string;
  icon: React.ReactNode;
}

function RiskItem({ label, count, total, color, icon }: RiskItemProps) {
  const percentage = total > 0 ? (count / total) * 100 : 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 font-mono text-sm">
          <span style={{ color }}>{icon}</span>
          <span className="text-[#e0e0e0]">{label}</span>
        </div>
        <span className="text-[#a0a0a0] font-mono text-sm">
          {count} ({percentage.toFixed(0)}%)
        </span>
      </div>
      <div className="w-full bg-[#1a1a1a] rounded-full h-2 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${percentage}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </div>
  );
}

function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'critical':
      return '#ef4444';
    case 'high':
      return '#f97316';
    case 'medium':
      return '#fbbf24';
    case 'low':
      return '#3b82f6';
    default:
      return '#6b7280';
  }
}
