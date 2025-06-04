'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { UploadCloud, FileText, Type } from 'lucide-react';
import Link from 'next/link';

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState(null);
  const [textContent, setTextContent] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [useTextInput, setUseTextInput] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const fileType = selectedFile.type;
      if (fileType === 'text/plain' || fileType === 'application/pdf') {
        setFile(selectedFile);
        setError(null);
      } else {
        setFile(null);
        setError('Please upload a .txt or .pdf file only.');
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!useTextInput && !file) {
      setError('Please select a file to upload.');
      return;
    }
    if (useTextInput && !textContent.trim()) {
      setError('Please enter some text content.');
      return;
    }
    
    setIsUploading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      if (useTextInput) {
        formData.append('text_content', textContent);
      } else if (file) {
        formData.append('file', file);
      }
      
      const uploadResponse = await fetch('http://localhost:8000/upload-content', {
        method: 'POST',
        body: formData,
      });
      
      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json().catch(() => ({ detail: uploadResponse.statusText }));
        throw new Error(errorData.detail || `Upload failed with status: ${uploadResponse.status}`);
      }
      
      const extractedContent = await uploadResponse.text();
      sessionStorage.setItem('uploadedContent', extractedContent);
      
      // No need to call /generate-diagnostic here, swipe page will do it.
      router.push('/swipe');
      
    } catch (err) {
      console.error('Error during upload process:', err);
      setError(err.message || 'An error occurred during the upload process.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div 
      className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center p-4 relative"
      style={{
        backgroundImage: "url('/assets/diagnostic-hallway.png')",
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundBlendMode: 'overlay',
        backgroundColor: 'rgba(0, 0, 0, 0.3)'
      }}
    >
      <div className="absolute top-6 left-6">
        <Link href="/" className="text-primary hover:underline flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-arrow-left"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
          Back to Home
        </Link>
      </div>
      <div className="bg-card text-card-foreground p-8 rounded-xl shadow-2xl w-full max-w-lg border border-border">
        <h2 className="text-3xl font-semibold text-center mb-8">Upload Your Learning Material</h2>
        
        <div className="mb-6 flex justify-center">
          <div className="inline-flex rounded-md shadow-sm bg-secondary p-1">
            <button
              type="button"
              onClick={() => setUseTextInput(false)}
              className={`px-6 py-2 text-sm font-medium rounded-md transition-colors
                ${!useTextInput ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-primary/10'}
              `}
            >
              <FileText className="inline-block mr-2 h-4 w-4" /> Upload File
            </button>
            <button
              type="button"
              onClick={() => setUseTextInput(true)}
              className={`px-6 py-2 text-sm font-medium rounded-md transition-colors
                ${useTextInput ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-primary/10'}
              `}
            >
              <Type className="inline-block mr-2 h-4 w-4" /> Paste Text
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-destructive/20 text-destructive rounded-md border border-destructive/50 text-sm">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {!useTextInput ? (
            <div className="space-y-2">
              <label htmlFor="fileInput" className="sr-only">Upload a file</label>
              <div className="relative border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/70 transition-colors cursor-pointer">
                <input
                  type="file"
                  accept=".txt,.pdf"
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  id="fileInput"
                  disabled={isUploading}
                />
                <UploadCloud className="mx-auto mb-3 text-muted-foreground h-12 w-12" />
                <p className="text-lg font-medium text-foreground">
                  Drag & drop or <span className="text-primary">click to upload</span>
                </p>
                <p className="text-sm text-muted-foreground mt-1">Supports .txt and .pdf files.</p>
                {file && (
                  <p className="mt-3 text-sm text-primary font-medium bg-primary/10 py-1 px-2 rounded-md inline-block">
                    Selected: {file.name}
                  </p>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <label htmlFor="textContentArea" className="sr-only">Enter text content</label>
              <textarea
                id="textContentArea"
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                placeholder="Paste or type your lecture notes, articles, or any text material here..."
                className="w-full h-48 p-4 border border-border rounded-lg bg-secondary text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-primary resize-none"
                disabled={isUploading}
              />
            </div>
          )}
          
          <button
            type="submit"
            disabled={isUploading || (!useTextInput && !file) || (useTextInput && !textContent.trim())}
            className="w-full py-3 px-4 bg-primary text-primary-foreground font-semibold rounded-lg transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
          >
            {isUploading ? (
              <div className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing Material...
              </div>
            ) : (
              'Generate Learning Quiz'
            )}
          </button>
        </form>
      </div>
    </div>
  );
} 