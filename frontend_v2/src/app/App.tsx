import { useState } from 'react';
import { FileUpload } from './components/FileUpload';
import { ChatInterface } from './components/ChatInterface';
import { LogViewer } from './components/LogViewer';
import { InsightsPanel } from './components/InsightsPanel';
import { analyzeLogFile, analyzeLogText, sendChatMessage } from './api';
import { ChatMessage, AnalysisReport } from './types';
import { Terminal, FileCode } from 'lucide-react';

function isLikelyLogText(content: string): boolean {
  const text = content.trim();
  if (!text) {
    return false;
  }

  if (text.includes('\n')) {
    return true;
  }

  return /\b(?:GET|POST|PUT|DELETE|PATCH|HTTP\/\d\.\d|\d{3}\s+\d+|\d{1,3}(?:\.\d{1,3}){3})\b/i.test(text);
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentReport, setCurrentReport] = useState<AnalysisReport | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleFileSelect = async (file: File) => {
    setIsAnalyzing(true);
    console.info('[workflow] step=frontend_file_selected', { fileName: file.name });

    // Add user message
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: `Analyzing file: ${file.name}`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      // Call API to analyze the log file
      const report = await analyzeLogFile(file);
      setCurrentReport(report);
      console.info('[workflow] step=frontend_report_updated_from_file', {
        warningCount: report.warnings.length,
      });

      // Add assistant response with report
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: `Analysis complete! I've found ${report.warnings.length} security warnings in your log file. The analysis reveals ${report.riskBreakdown.critical} critical issues, ${report.riskBreakdown.high} high-priority issues, ${report.riskBreakdown.medium} medium-priority issues, and ${report.riskBreakdown.low} low-priority issues.\n\nYou can review the detailed insights in the panel on the right, and see the highlighted log contents below. Feel free to ask me any questions about the findings!`,
        timestamp: new Date(),
        report,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      // Handle error
      const errorMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: 'Sorry, there was an error analyzing the log file. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    setIsProcessing(true);
    console.info('[workflow] step=frontend_chat_message_received', {
      contentLength: content.length,
    });

    // Add user message
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      if (isLikelyLogText(content)) {
        console.info('[workflow] step=frontend_chat_log_analysis_started');
        const report = await analyzeLogText(content);
        setCurrentReport(report);

        const assistantMessage: ChatMessage = {
          id: `msg_${Date.now() + 1}`,
          role: 'assistant',
          content: `Analyzed pasted text successfully. Found ${report.warnings.length} warnings across ${report.logs.length} lines. Check the right panel for severity and redaction hints.`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
        console.info('[workflow] step=frontend_chat_log_analysis_completed', {
          warningCount: report.warnings.length,
        });
        return;
      }

      // Send message to API
      const response = await sendChatMessage(content, currentReport?.id, currentReport, messages);

      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      console.info('[workflow] step=frontend_chat_response_received');
    } catch (error) {
      // Handle error
      const errorMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      console.error('[workflow] step=frontend_chat_error', error);
    } finally {
      setIsProcessing(false);
      console.info('[workflow] step=frontend_chat_processing_finished');
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#e0e0e0]">
      {/* Header */}
      <header className="border-b border-[#2a2a2a] bg-[#0d0d0d]">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="flex items-start gap-3">
            <Terminal className="w-6 h-6 text-[#8b5cf6] mt-1" />
            <div>
              <h1 className="font-mono text-xl">LogGuard 👾</h1>
              <p className="text-xs text-[#9ca3af] font-mono mt-1">
                Detect sensitive data leaks in logs and get actionable AI security insights.
              </p>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-[1800px] mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content - Left/Center Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* File Upload */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <FileCode className="w-5 h-5 text-[#8b5cf6]" />
                <h2 className="font-mono text-lg">Upload Log File</h2>
              </div>
              <FileUpload onFileSelect={handleFileSelect} isAnalyzing={isAnalyzing} />
            </div>

            {/* Chat Interface */}
            <div className="h-[400px]">
              <ChatInterface
                messages={messages}
                onSendMessage={handleSendMessage}
                isProcessing={isProcessing}
              />
            </div>

            {/* Log Viewer */}
            {currentReport && (
              <div>
                <LogViewer logs={currentReport.logs} />
              </div>
            )}
          </div>

          {/* Insights Panel - Right Column */}
          <div className="lg:col-span-1">
            {currentReport ? (
              <InsightsPanel report={currentReport} />
            ) : (
              <div className="bg-[#0d0d0d] rounded-lg border border-[#2a2a2a] p-8">
                <div className="text-center text-[#666] font-mono">
                  <Terminal className="w-16 h-16 mx-auto mb-4 opacity-30" />
                  <p className="text-sm">No analysis available</p>
                  <p className="text-xs mt-2">Upload a log file to see insights</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-[#2a2a2a] bg-[#0d0d0d] mt-12">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <p className="text-xs text-[#666] font-mono text-center">
            LogGuard. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
