export interface LogLine {
  lineNumber: number;
  content: string;
  isSensitive: boolean;
  riskLevel?: 'low' | 'medium' | 'high' | 'critical';
}

export interface SecurityWarning {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  lineNumbers: number[];
  redactionHint?: string;
}

export interface RiskBreakdown {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface AnalysisReport {
  id: string;
  fileName: string;
  timestamp: string;
  summary: string;
  logs: LogLine[];
  warnings: SecurityWarning[];
  riskBreakdown: RiskBreakdown;
  aiSummary: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  report?: AnalysisReport;
}
