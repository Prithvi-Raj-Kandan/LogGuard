import { AnalysisReport } from './types';

type BackendRiskLevel = 'low' | 'medium' | 'high' | 'critical';

interface BackendFinding {
  type: string;
  risk: BackendRiskLevel;
  line?: number;
  value?: string;
  redaction_hint?: string;
}

interface BackendAnalyzeResponse {
  summary: string;
  content_type: string;
  findings: BackendFinding[];
  risk_score: number;
  risk_level: BackendRiskLevel;
  action: string;
  insights: string[];
  metadata?: {
    file_name?: string;
    file_suffix?: string;
    line_count?: number;
    chunk_count?: number;
    warnings?: string[];
    log_type?: string;
    log_sub_type?: string;
    request_id?: string;
    processing_time_ms?: number;
  };
}

const viteEnv = (import.meta as ImportMeta & {
  env?: Record<string, string | undefined>;
}).env;

const FASTAPI_BASE_URL = viteEnv?.VITE_API_BASE_URL?.trim() || 'http://localhost:8000';

function buildRiskBreakdown(findings: BackendFinding[]) {
  return findings.reduce(
    (acc, finding) => {
      acc[finding.risk] += 1;
      return acc;
    },
    {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
    }
  );
}

function buildWarnings(findings: BackendFinding[]) {
  return findings.map((finding, idx) => ({
    id: `w_${idx + 1}`,
    type: finding.type,
    severity: finding.risk,
    message: `${finding.type} detected${finding.line ? ` at line ${finding.line}` : ''}`,
    lineNumbers: finding.line ? [finding.line] : [],
    redactionHint: finding.redaction_hint,
  }));
}

function buildLogLinesFromText(fileText: string, findings: BackendFinding[]) {
  const riskyLineMap = new Map<number, BackendRiskLevel>();
  findings.forEach((finding) => {
    if (!finding.line) {
      return;
    }
    const existing = riskyLineMap.get(finding.line);
    if (!existing || severityRank(finding.risk) > severityRank(existing)) {
      riskyLineMap.set(finding.line, finding.risk);
    }
  });

  return fileText.split(/\r?\n/).map((content, idx) => {
    const lineNumber = idx + 1;
    const riskLevel = riskyLineMap.get(lineNumber);
    return {
      lineNumber,
      content,
      isSensitive: Boolean(riskLevel),
      riskLevel,
    };
  });
}

function severityRank(severity: BackendRiskLevel): number {
  switch (severity) {
    case 'critical':
      return 4;
    case 'high':
      return 3;
    case 'medium':
      return 2;
    case 'low':
    default:
      return 1;
  }
}

/**
 * Upload log file to FastAPI backend for analysis
 * 
 * FastAPI Endpoint Example:
 * POST /api/analyze
 * Content-Type: multipart/form-data
 * Body: { file: File }
 * 
 * Response: AnalysisReport
 */
export async function analyzeLogFile(file: File): Promise<AnalysisReport> {
  console.info('[workflow] step=frontend_analyze_upload_started', {
    fileName: file.name,
    fileSize: file.size,
    fileType: file.type,
  });

  const formData = new FormData();
  formData.append('file', file);
  formData.append('mask', 'true');
  formData.append('block_high_risk', 'false');
  formData.append('log_analysis', 'true');
  
  const response = await fetch(`${FASTAPI_BASE_URL}/analyze/upload`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message =
      errorBody?.detail?.message ||
      errorBody?.detail ||
      'Failed to analyze log file';
    throw new Error(message);
  }
  
  const backend = (await response.json()) as BackendAnalyzeResponse;
  console.info('[workflow] step=frontend_analyze_upload_completed', {
    findings: backend.findings?.length ?? 0,
    logType: backend.metadata?.log_type,
    requestId: backend.metadata?.request_id,
  });
  const fileText = await file.text();
  const findings = backend.findings || [];

  return {
    id: `report_${Date.now()}`,
    fileName: backend.metadata?.file_name || file.name,
    timestamp: new Date().toISOString(),
    summary: backend.summary,
    logs: buildLogLinesFromText(fileText, findings),
    warnings: buildWarnings(findings),
    riskBreakdown: buildRiskBreakdown(findings),
    aiSummary:
      backend.insights?.join('\n') ||
      'No AI insights available yet. Upload parsing is connected and operational.',
  };
}

export async function analyzeLogText(text: string): Promise<AnalysisReport> {
  console.info('[workflow] step=frontend_analyze_text_started', {
    contentLength: text.length,
  });

  const response = await fetch(`${FASTAPI_BASE_URL}/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      input_type: 'log',
      content: text,
      options: {
        mask: true,
        block_high_risk: false,
        log_analysis: true,
      },
    }),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message =
      errorBody?.detail?.message ||
      errorBody?.detail ||
      'Failed to analyze pasted log text';
    throw new Error(message);
  }

  const backend = (await response.json()) as BackendAnalyzeResponse;
  const findings = backend.findings || [];

  console.info('[workflow] step=frontend_analyze_text_completed', {
    findings: findings.length,
    logType: backend.metadata?.log_type,
    requestId: backend.metadata?.request_id,
  });

  return {
    id: `report_${Date.now()}`,
    fileName: backend.metadata?.file_name || 'pasted_log_text',
    timestamp: new Date().toISOString(),
    summary: backend.summary,
    logs: buildLogLinesFromText(text, findings),
    warnings: buildWarnings(findings),
    riskBreakdown: buildRiskBreakdown(findings),
    aiSummary:
      backend.insights?.join('\n') ||
      'No AI insights available yet. Text parsing is connected and operational.',
  };
}

/**
 * Send chat message to FastAPI backend
 * 
 * FastAPI Endpoint Example:
 * POST /api/chat
 * Content-Type: application/json
 * Body: { message: string, reportId?: string }
 * 
 * Response: { response: string }
 */
export async function sendChatMessage(message: string, reportId?: string): Promise<string> {
  // PRODUCTION: Uncomment this code to connect to your FastAPI backend
  /*
  const response = await fetch(`${FASTAPI_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, reportId }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to send chat message');
  }
  
  const data = await response.json();
  return data.response;
  */

  // Backend chat endpoint is not implemented yet.
  // Keep this fallback until LG chat integration ticket is completed.
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(generateMockChatResponse(message));
    }, 1000);
  });
}

// ============================================================================
// MOCK DATA GENERATION (Remove when connecting to real backend)
// ============================================================================

function generateMockChatResponse(message: string): string {
  const responses = [
    "I've analyzed your log file. The main concerns are related to credential exposure and SQL injection attempts. Would you like me to explain any specific warning?",
    "Based on the log analysis, I recommend prioritizing the critical security warnings first, particularly the default credentials and SQL injection vulnerabilities.",
    "The authentication failures on line 5 indicate potential brute force attempts. Consider implementing rate limiting or IP-based blocking.",
    "Looking at the risk breakdown, you have 2 critical issues that need immediate attention. I can provide detailed remediation steps if needed.",
  ];
  
  return responses[Math.floor(Math.random() * responses.length)];
}
