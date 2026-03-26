import { useState } from 'react';
import { AnalysisReport } from '../types';
import {
  Brain,
  AlertTriangle,
  XCircle,
  AlertCircle,
  Shield,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';

interface InsightsPanelProps {
  report: AnalysisReport;
}

export function InsightsPanel({ report }: InsightsPanelProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    critical: true,
    high: true,
    medium: false,
    low: false,
  });

  const totalRisks = 
    report.riskBreakdown.critical +
    report.riskBreakdown.high +
    report.riskBreakdown.medium +
    report.riskBreakdown.low;

  const warningsBySeverity = {
    critical: report.warnings.filter((w) => w.severity === 'critical'),
    high: report.warnings.filter((w) => w.severity === 'high'),
    medium: report.warnings.filter((w) => w.severity === 'medium'),
    low: report.warnings.filter((w) => w.severity === 'low'),
  };

  const toggle = (severity: 'critical' | 'high' | 'medium' | 'low') => {
    setExpanded((prev) => ({ ...prev, [severity]: !prev[severity] }));
  };

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

      {/* Security Warnings (Merged Risk Breakdown + Warning Details) */}
      <div className="bg-[#0d0d0d] rounded-lg border border-[#2a2a2a] overflow-hidden">
        <div className="bg-[#1a1a1a] px-4 py-3 border-b border-[#2a2a2a]">
          <h3 className="text-[#e0e0e0] font-mono flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-[#f97316]" />
            Security Warnings ({report.warnings.length})
          </h3>
        </div>
        <div className="p-4 space-y-3 max-h-[400px] overflow-y-auto">
          <SeveritySection
            label="Critical"
            severity="critical"
            count={report.riskBreakdown.critical}
            total={totalRisks}
            color="#ef4444"
            icon={<XCircle className="w-4 h-4" />}
            warnings={warningsBySeverity.critical}
            expanded={expanded.critical}
            onToggle={() => toggle('critical')}
          />
          <SeveritySection
            label="High"
            severity="high"
            count={report.riskBreakdown.high}
            total={totalRisks}
            color="#f97316"
            icon={<AlertTriangle className="w-4 h-4" />}
            warnings={warningsBySeverity.high}
            expanded={expanded.high}
            onToggle={() => toggle('high')}
          />
          <SeveritySection
            label="Medium"
            severity="medium"
            count={report.riskBreakdown.medium}
            total={totalRisks}
            color="#fbbf24"
            icon={<AlertCircle className="w-4 h-4" />}
            warnings={warningsBySeverity.medium}
            expanded={expanded.medium}
            onToggle={() => toggle('medium')}
          />
          <SeveritySection
            label="Low"
            severity="low"
            count={report.riskBreakdown.low}
            total={totalRisks}
            color="#3b82f6"
            icon={<Shield className="w-4 h-4" />}
            warnings={warningsBySeverity.low}
            expanded={expanded.low}
            onToggle={() => toggle('low')}
          />
        </div>
      </div>
    </div>
  );
}

interface SeveritySectionProps {
  label: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  count: number;
  total: number;
  color: string;
  icon: React.ReactNode;
  warnings: AnalysisReport['warnings'];
  expanded: boolean;
  onToggle: () => void;
}

function SeveritySection({
  label,
  severity,
  count,
  total,
  color,
  icon,
  warnings,
  expanded,
  onToggle,
}: SeveritySectionProps) {
  const percentage = total > 0 ? (count / total) * 100 : 0;

  return (
    <div className="bg-[#141414] border border-[#242424] rounded">
      <button
        type="button"
        onClick={onToggle}
        className="w-full p-3 text-left"
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 font-mono text-sm">
            <span style={{ color }}>{icon}</span>
            <span className="text-[#e0e0e0]">{label}</span>
            <span
              className="text-xs px-2 py-0.5 rounded font-mono"
              style={{
                backgroundColor: `${color}20`,
                color,
              }}
            >
              {count}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[#a0a0a0] font-mono text-sm">
              {percentage.toFixed(0)}%
            </span>
            {expanded ? (
              <ChevronDown className="w-4 h-4 text-[#a0a0a0]" />
            ) : (
              <ChevronRight className="w-4 h-4 text-[#a0a0a0]" />
            )}
          </div>
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
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-2">
          {warnings.length === 0 ? (
            <div className="p-2 text-xs font-mono text-[#777] bg-[#101010] rounded border border-[#1f1f1f]">
              No {severity} warnings.
            </div>
          ) : (
            warnings.map((warning) => (
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
            ))
          )}
        </div>
      )}
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
