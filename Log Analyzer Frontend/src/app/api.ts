import { AnalysisReport } from './types';

// ============================================================================
// FASTAPI BACKEND INTEGRATION
// ============================================================================
// Replace this with your actual FastAPI backend URL
const FASTAPI_BASE_URL = 'http://localhost:8000'; // Update this to your backend URL

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
  // PRODUCTION: Uncomment this code to connect to your FastAPI backend
  /*
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${FASTAPI_BASE_URL}/api/analyze`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    throw new Error('Failed to analyze log file');
  }
  
  return await response.json();
  */

  // MOCK: Remove this mock implementation when connecting to your backend
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(generateMockReport(file.name));
    }, 2000); // Simulate API delay
  });
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

  // MOCK: Remove this mock implementation when connecting to your backend
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(generateMockChatResponse(message));
    }, 1000);
  });
}

// ============================================================================
// MOCK DATA GENERATION (Remove when connecting to real backend)
// ============================================================================

function generateMockReport(fileName: string): AnalysisReport {
  const mockLogs = [
    { lineNumber: 1, content: '[2026-03-24 10:15:32] INFO: Application started successfully', isSensitive: false },
    { lineNumber: 2, content: '[2026-03-24 10:15:33] INFO: Connecting to database...', isSensitive: false },
    { lineNumber: 3, content: '[2026-03-24 10:15:34] WARN: Using default admin credentials: admin/password123', isSensitive: true, riskLevel: 'critical' },
    { lineNumber: 4, content: '[2026-03-24 10:15:35] INFO: Database connection established', isSensitive: false },
    { lineNumber: 5, content: '[2026-03-24 10:15:40] ERROR: Failed authentication attempt from IP: 192.168.1.100', isSensitive: true, riskLevel: 'high' },
    { lineNumber: 6, content: '[2026-03-24 10:15:45] INFO: User login successful - user@example.com', isSensitive: true, riskLevel: 'medium' },
    { lineNumber: 7, content: '[2026-03-24 10:16:00] WARN: Deprecated API endpoint accessed', isSensitive: false, riskLevel: 'low' },
    { lineNumber: 8, content: '[2026-03-24 10:16:15] INFO: Processing request...', isSensitive: false },
    { lineNumber: 9, content: '[2026-03-24 10:16:20] ERROR: SQL Injection attempt detected: SELECT * FROM users WHERE id=1 OR 1=1', isSensitive: true, riskLevel: 'critical' },
    { lineNumber: 10, content: '[2026-03-24 10:16:25] INFO: Request processed successfully', isSensitive: false },
    { lineNumber: 11, content: '[2026-03-24 10:16:30] WARN: High memory usage detected: 89%', isSensitive: false, riskLevel: 'medium' },
    { lineNumber: 12, content: '[2026-03-24 10:16:35] INFO: Cache cleared', isSensitive: false },
    { lineNumber: 13, content: '[2026-03-24 10:16:40] ERROR: Unhandled exception in module auth.py', isSensitive: true, riskLevel: 'high' },
    { lineNumber: 14, content: '[2026-03-24 10:16:45] INFO: System health check passed', isSensitive: false },
    { lineNumber: 15, content: '[2026-03-24 10:17:00] WARN: SSL certificate expires in 7 days', isSensitive: true, riskLevel: 'high' },
  ];

  const mockWarnings = [
    {
      id: 'w1',
      type: 'Credentials Exposure',
      severity: 'critical' as const,
      message: 'Default credentials detected in logs. This poses a severe security risk.',
      lineNumbers: [3],
    },
    {
      id: 'w2',
      type: 'SQL Injection',
      severity: 'critical' as const,
      message: 'SQL injection attempt detected. Immediate action required.',
      lineNumbers: [9],
    },
    {
      id: 'w3',
      type: 'Authentication Failure',
      severity: 'high' as const,
      message: 'Multiple failed authentication attempts detected from suspicious IP.',
      lineNumbers: [5],
    },
    {
      id: 'w4',
      type: 'SSL Certificate',
      severity: 'high' as const,
      message: 'SSL certificate expiring soon. Renewal required.',
      lineNumbers: [15],
    },
    {
      id: 'w5',
      type: 'System Error',
      severity: 'high' as const,
      message: 'Unhandled exception in authentication module.',
      lineNumbers: [13],
    },
  ];

  return {
    id: `report_${Date.now()}`,
    fileName,
    timestamp: new Date().toISOString(),
    summary: `Analyzed ${fileName} - Found ${mockWarnings.length} security warnings`,
    logs: mockLogs,
    warnings: mockWarnings,
    riskBreakdown: {
      critical: 2,
      high: 3,
      medium: 2,
      low: 1,
    },
    aiSummary: `Analysis of ${fileName} reveals several critical security concerns:\n\n1. **Credential Exposure**: Default admin credentials (admin/password123) are being used and logged, creating a severe security vulnerability.\n\n2. **SQL Injection Attack**: A SQL injection attempt was detected and logged, indicating potential vulnerability in the application's input validation.\n\n3. **Authentication Issues**: Failed login attempts from IP 192.168.1.100 suggest possible brute force attack attempts.\n\n4. **SSL Certificate Expiration**: The SSL certificate is expiring in 7 days, which could lead to service disruption.\n\n5. **System Errors**: Unhandled exceptions in the authentication module indicate potential stability issues.\n\nRecommendations:\n- Immediately change default credentials and implement strong password policies\n- Review and strengthen input validation to prevent SQL injection\n- Implement rate limiting and IP blocking for failed authentication attempts\n- Renew SSL certificate before expiration\n- Debug and fix authentication module errors`,
  };
}

function generateMockChatResponse(message: string): string {
  const responses = [
    "I've analyzed your log file. The main concerns are related to credential exposure and SQL injection attempts. Would you like me to explain any specific warning?",
    "Based on the log analysis, I recommend prioritizing the critical security warnings first, particularly the default credentials and SQL injection vulnerabilities.",
    "The authentication failures on line 5 indicate potential brute force attempts. Consider implementing rate limiting or IP-based blocking.",
    "Looking at the risk breakdown, you have 2 critical issues that need immediate attention. I can provide detailed remediation steps if needed.",
  ];
  
  return responses[Math.floor(Math.random() * responses.length)];
}
