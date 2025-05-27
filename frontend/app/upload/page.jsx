'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { UploadCloud } from 'lucide-react';
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
      // Check if file is .txt or .pdf
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
    
    // Validate that either file or text is provided
    if (!file && !textContent && !useTextInput) {
      setError('Please upload a file or switch to text input.');
      return;
    }
    
    if (useTextInput && !textContent) {
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
      
      // Upload content to backend
      const uploadResponse = await fetch('http://localhost:8000/upload-content', {
        method: 'POST',
        body: formData,
      });
      
      if (!uploadResponse.ok) {
        throw new Error(`Upload failed with status: ${uploadResponse.status}`);
      }
      
      // Get the extracted content
      const extractedContent = await uploadResponse.text();
      
      // Store the content in sessionStorage for the swipe page to use
      sessionStorage.setItem('uploadedContent', extractedContent);
      
      // Generate diagnostic questions based on the extracted content
      const diagnosticResponse = await fetch('http://localhost:8000/generate-diagnostic', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: extractedContent }),
      });
      
      if (!diagnosticResponse.ok) {
        throw new Error(`Diagnostic generation failed with status: ${diagnosticResponse.status}`);
      }
      
      // Redirect to the swipe page
      router.push('/swipe');
      
    } catch (err) {
      console.error('Error during upload process:', err);
      setError(err.message || 'An error occurred during the upload process.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-zinc-950 text-white">
      <header className="bg-zinc-900 p-4 shadow-md">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">JiaranAI Learning Lab</h1>
          <Link href="/" className="text-violet-400 hover:text-violet-300">
            Home
          </Link>
        </div>
      </header>

      <main className="flex-grow flex items-center justify-center p-4">
        <div className="bg-zinc-900 p-6 rounded-2xl shadow-xl max-w-md w-full">
          <h1 className="text-2xl font-bold mb-6 text-center">Upload Content</h1>
          
          {error && (
            <div className="mb-4 p-3 bg-red-900/40 text-red-300 rounded-md border border-red-700">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="flex items-center mb-4">
              <button
                type="button"
                className={`flex-1 py-2 px-4 text-center ${!useTextInput ? 'bg-violet-700 text-white' : 'bg-zinc-800 text-zinc-400'} rounded-l-md`}
                onClick={() => setUseTextInput(false)}
              >
                File Upload
              </button>
              <button
                type="button"
                className={`flex-1 py-2 px-4 text-center ${useTextInput ? 'bg-violet-700 text-white' : 'bg-zinc-800 text-zinc-400'} rounded-r-md`}
                onClick={() => setUseTextInput(true)}
              >
                Text Input
              </button>
            </div>
            
            {!useTextInput ? (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-zinc-300">
                  Upload a file (.txt or .pdf)
                </label>
                <div className="border border-zinc-700 p-6 rounded-lg text-center cursor-pointer hover:border-violet-500 transition-colors">
                  <input
                    type="file"
                    accept=".txt,.pdf"
                    onChange={handleFileChange}
                    className="hidden"
                    id="fileInput"
                  />
                  <label htmlFor="fileInput" className="cursor-pointer block">
                    <UploadCloud className="mx-auto mb-2 text-zinc-500" size={40} />
                    <p className="text-zinc-400">Drag & drop or click to upload</p>
                    {file && (
                      <p className="mt-2 text-violet-400">
                        Selected file: {file.name}
                      </p>
                    )}
                  </label>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-zinc-300">
                  Enter text content
                </label>
                <textarea
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  placeholder="Paste or type your content here..."
                  className="w-full h-40 p-3 border border-zinc-700 rounded-lg bg-zinc-800 text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>
            )}
            
            <button
              type="submit"
              disabled={isUploading}
              className="w-full py-3 px-4 bg-violet-600 hover:bg-violet-700 text-white font-semibold rounded-xl transition duration-200 disabled:bg-violet-900 disabled:text-violet-300"
            >
              {isUploading ? (
                <div className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing...
                </div>
              ) : (
                'Upload & Generate Questions'
              )}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
} 