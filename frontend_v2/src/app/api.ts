import { AnalysisReport, ChatMessage } from './types';

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
  processed_content?: string;
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

function resolveApiBaseUrl(rawValue?: string): string {
  const raw = (rawValue || '').trim();
  if (!raw) {
    return 'http://localhost:8000';
  }

  const withProtocol = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
  return withProtocol.replace(/\/+$/, '');
}

const FASTAPI_BASE_URL = resolveApiBaseUrl(viteEnv?.VITE_API_BASE_URL);

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
  if (!fileText) {
    return [];
  }

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

function resolveDisplayText(backend: BackendAnalyzeResponse, fallbackText: string): string {
  if (backend.action === 'blocked') {
    return '';
  }

  const processed = backend.processed_content?.trim();
  if (processed) {
    return processed;
  }

  return fallbackText;
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
  const displayText = resolveDisplayText(backend, fileText);
  const findings = backend.findings || [];

  return {
    id: `report_${Date.now()}`,
    fileName: backend.metadata?.file_name || file.name,
    timestamp: new Date().toISOString(),
    summary: backend.summary,
    logs: buildLogLinesFromText(displayText, findings),
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
  const displayText = resolveDisplayText(backend, text);
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
    logs: buildLogLinesFromText(displayText, findings),
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
export async function sendChatMessage(
  message: string,
  reportId?: string,
  report?: AnalysisReport | null,
  history: ChatMessage[] = []
): Promise<string> {
  const compactHistory = history.slice(-10).map((item) => ({
    role: item.role,
    content: item.content,
  }));

  try {
    const response = await fetch(`${FASTAPI_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        report_id: reportId,
        report,
        history: compactHistory,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to send chat message');
    }

    const data = (await response.json()) as { response?: string };
    if (data.response?.trim()) {
      return data.response;
    }
    throw new Error('Invalid chat response payload');
  } catch (error) {
    console.warn('[workflow] step=frontend_chat_fallback_due_to_error', {
      error: error instanceof Error ? error.message : String(error),
    });
    return generateContextualChatResponse(message, report, history);
  }
}

// ============================================================================
// CONTEXTUAL FALLBACK CHAT (Remove when connecting to real backend)
// ============================================================================

function generateContextualChatResponse(
  message: string,
  report?: AnalysisReport | null,
  history: ChatMessage[] = []
): string {
  const query = message.toLowerCase();

  if (!report) {
    return 'I do not have an analysis report in context yet. Upload a log file or paste log text first.';
  }

  const warnings = report.warnings || [];
  const criticalWarnings = warnings.filter((item) => item.severity === 'critical');
  const highWarnings = warnings.filter((item) => item.severity === 'high');
  const orderedWarnings = [...criticalWarnings, ...highWarnings, ...warnings.filter((item) => item.severity !== 'critical' && item.severity !== 'high')];

  const previousAssistant = [...history]
    .reverse()
    .find((item) => item.role === 'assistant' && item.content);

  if (warnings.length === 0) {
    return 'This report has no detected sensitive warnings, so there is no critical breach to prioritize.';
  }

  if (query.includes('most critical') || query.includes('critical security breach') || query.includes('highest risk')) {
    const top = orderedWarnings[0];
    return `The highest-risk finding is ${top.type} (${top.severity})${top.lineNumbers.length ? ` at line ${top.lineNumbers.join(', ')}` : ''}. Prioritize secret rotation and immediate redaction for this data.`;
  }

  if (query.includes('3 critical') || query.includes('three critical') || query.includes('top 3')) {
    const topThree = orderedWarnings.slice(0, 3);
    const lines = topThree.map((item, index) => {
      const lineRef = item.lineNumbers.length ? `line ${item.lineNumbers.join(', ')}` : 'line unknown';
      const hint = item.redactionHint ? ` Redaction: ${item.redactionHint}.` : '';
      return `${index + 1}. ${item.type} (${item.severity}) on ${lineRef}.${hint}`;
    });
    return `Top 3 highest-priority warnings:\n${lines.join('\n')}`;
  }

  const requestedLine = query.match(/line\s+(\d+)/);
  if (requestedLine) {
    const lineNumber = Number(requestedLine[1]);
    const lineWarnings = warnings.filter((item) => item.lineNumbers.includes(lineNumber));
    if (!lineWarnings.length) {
      return `No warning is currently mapped to line ${lineNumber} in this report.`;
    }

    const details = lineWarnings
      .map((item) => `${item.type} (${item.severity})${item.redactionHint ? `, redaction ${item.redactionHint}` : ''}`)
      .join('; ');
    return `Line ${lineNumber} includes: ${details}.`;
  }

  if (query.includes('summary') || query.includes('overview') || query.includes('risk breakdown')) {
    const rb = report.riskBreakdown;
    return `Risk summary for ${report.fileName}: critical=${rb.critical}, high=${rb.high}, medium=${rb.medium}, low=${rb.low}. Total warnings=${warnings.length}.`;
  }

  if (query.includes('why') && previousAssistant) {
    return `Using the current report context, I prioritized by severity and line evidence. ${previousAssistant.content}`;
  }

  const first = orderedWarnings[0];
  return `I am using the current report context. Start with ${first.type} (${first.severity})${first.lineNumbers.length ? ` at line ${first.lineNumbers.join(', ')}` : ''}, then I can walk through each warning in order.`;
}
