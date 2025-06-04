import Link from 'next/link';
import { BookOpen, UploadCloud, MessageSquare, Zap, Users } from 'lucide-react';
import Image from 'next/image';

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center p-4">
      <header className="absolute top-0 left-0 right-0 p-6 flex justify-between items-center">
        <div className="flex items-center gap-2">
          {/* Ensure this path is correct or update if you place the logo elsewhere */}
          <Image src="/assets/logos/JiaranAI.png" alt="JiaranAI Logo" width={240} height={240} />
        </div>
        {/* Future: Dark mode toggle or user profile could go here */}
      </header>

      <main className="text-center space-y-10 max-w-4xl w-full">
        <div className="space-y-3">
          <h2 className="text-5xl font-bold tracking-tight">
            Unlock Your Potential with <span className="text-primary">AI-Powered Learning</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Upload your course materials, get instant diagnostic quizzes, and engage in simulated classroom discussions to master any subject.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard
            href="/upload"
            icon={<UploadCloud className="h-10 w-10 mb-4 text-primary" />}
            title="Upload Content"
            description="Securely upload your lecture notes, PDFs, or text. We process it instantly."
          />
          <FeatureCard
            href="/swipe"
            icon={<Zap className="h-10 w-10 mb-4 text-primary" />}
            title="Diagnostic Quizzes"
            description="Test your understanding with adaptive, swipe-style questions generated from your content."
          />
          <FeatureCard
            href="/classroom"
            icon={<Users className="h-10 w-10 mb-4 text-primary" />}
            title="AI Classroom"
            description="Deepen your knowledge by discussing topics with our AI-powered virtual classmates."
          />
        </div>

        <div className="pt-8">
          <Link 
            href="/upload" 
            className="bg-primary text-primary-foreground hover:bg-primary/90 font-semibold py-3 px-8 rounded-lg text-lg transition-colors shadow-lg hover:shadow-primary/40"
          >
            Get Started Now
          </Link>
        </div>
      </main>

      <footer className="absolute bottom-0 left-0 right-0 p-6 text-center text-muted-foreground text-sm">
        <p>© {new Date().getFullYear()} JiaranAI Learning Lab. All rights reserved.</p>
      </footer>
    </div>
  );
}

interface FeatureCardProps {
  href: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}

function FeatureCard({ href, icon, title, description }: FeatureCardProps) {
  return (
    <Link 
      href={href} 
      className="bg-card text-card-foreground p-6 rounded-lg border border-border hover:border-primary/50 hover:shadow-xl hover:shadow-primary/20 transition-all transform hover:-translate-y-1 flex flex-col items-center text-center"
    >
      {icon}
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </Link>
  );
} 