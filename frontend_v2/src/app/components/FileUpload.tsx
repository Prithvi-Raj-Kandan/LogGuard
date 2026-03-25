import { useCallback, useState } from 'react';
import { Upload, FileText, X } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isAnalyzing: boolean;
}

export function FileUpload({ onFileSelect, isAnalyzing }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const allowedExtensions = ['.log', '.txt', '.pdf', '.doc', '.docx'];

  const isAcceptedFile = (file: File) => {
    const lowerName = file.name.toLowerCase();
    return allowedExtensions.some((ext) => lowerName.endsWith(ext));
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const logFile = files.find((file) => isAcceptedFile(file));

    if (logFile) {
      setSelectedFile(logFile);
      onFileSelect(logFile);
    }
  }, [onFileSelect]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && isAcceptedFile(file)) {
      setSelectedFile(file);
      onFileSelect(file);
    }
  }, [onFileSelect]);

  const handleClearFile = useCallback(() => {
    setSelectedFile(null);
  }, []);

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-lg p-8 transition-all
          ${isDragging 
            ? 'border-[#8b5cf6] bg-[#8b5cf6]/10' 
            : 'border-[#3a3a3a] bg-[#1a1a1a] hover:border-[#4a4a4a]'
          }
          ${isAnalyzing ? 'opacity-50 pointer-events-none' : ''}
        `}
      >
        {selectedFile ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-[#8b5cf6]" />
              <div>
                <p className="text-[#e0e0e0] font-mono">{selectedFile.name}</p>
                <p className="text-sm text-[#888] font-mono">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
            </div>
            {!isAnalyzing && (
              <button
                onClick={handleClearFile}
                className="p-2 hover:bg-[#2a2a2a] rounded transition-colors"
              >
                <X className="w-5 h-5 text-[#888]" />
              </button>
            )}
          </div>
        ) : (
          <div className="text-center">
            <Upload className="w-12 h-12 mx-auto mb-4 text-[#666]" />
            <p className="text-[#e0e0e0] mb-2 font-mono">
              Drag & drop your log file here
            </p>
            <p className="text-sm text-[#888] mb-4 font-mono">
              Supports .log, .txt, .pdf, .doc and .docx files
            </p>
            <label className="inline-block">
              <input
                type="file"
                accept="*/*"
                onChange={handleFileChange}
                className="hidden"
                disabled={isAnalyzing}
              />
              <span className="inline-flex items-center gap-2 px-4 py-2 bg-[#8b5cf6] text-white rounded font-mono cursor-pointer hover:bg-[#7c3aed] transition-colors">
                <Upload className="w-4 h-4" />
                Browse Files
              </span>
            </label>
          </div>
        )}
      </div>

      {isAnalyzing && (
        <div className="mt-4 flex items-center gap-2 text-[#888] font-mono text-sm">
          <div className="w-4 h-4 border-2 border-[#8b5cf6] border-t-transparent rounded-full animate-spin" />
          Analyzing log file...
        </div>
      )}
    </div>
  );
}
