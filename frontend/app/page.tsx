import Image from "next/image";
import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-950 text-white flex flex-col">
      <header className="p-6 border-b border-zinc-800">
        <h1 className="text-3xl font-bold text-center text-white">JiaranAI <span className="text-violet-400">Learning Lab</span></h1>
      </header>

      <main className="flex-grow flex flex-col items-center justify-center p-8 md:p-16">
        <div className="max-w-3xl w-full space-y-12">
          <div className="text-center space-y-4">
            <h2 className="text-4xl font-bold">Interactive AI Learning</h2>
            <p className="text-xl text-zinc-400">Explore, learn, and test your knowledge with our AI-powered learning tools</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Link 
              href="/upload" 
              className="bg-zinc-800 hover:bg-zinc-700 p-6 rounded-xl border border-zinc-700 transition-all hover:shadow-lg hover:shadow-violet-900/20 group"
            >
              <h3 className="text-xl font-bold mb-2 group-hover:text-violet-400">Upload Content</h3>
              <p className="text-zinc-400">Upload lecture notes or text to generate personalized learning materials</p>
            </Link>
            
            <Link 
              href="/swipe" 
              className="bg-zinc-800 hover:bg-zinc-700 p-6 rounded-xl border border-zinc-700 transition-all hover:shadow-lg hover:shadow-violet-900/20 group"
            >
              <h3 className="text-xl font-bold mb-2 group-hover:text-violet-400">Swipe Diagnostics</h3>
              <p className="text-zinc-400">Test your knowledge with AI-generated diagnostic questions</p>
            </Link>
            
            <Link 
              href="/classroom" 
              className="bg-zinc-800 hover:bg-zinc-700 p-6 rounded-xl border border-zinc-700 transition-all hover:shadow-lg hover:shadow-violet-900/20 group"
            >
              <h3 className="text-xl font-bold mb-2 group-hover:text-violet-400">AI Classroom</h3>
              <p className="text-zinc-400">Engage in discussions with AI characters to deepen your understanding</p>
            </Link>
          </div>
        </div>
      </main>

      <footer className="border-t border-zinc-800 p-6 text-center text-zinc-500 text-sm">
        <p>© 2023 JiaranAI Learning Lab. All rights reserved.</p>
      </footer>
    </div>
  );
}
