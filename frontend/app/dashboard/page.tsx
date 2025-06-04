import Link from 'next/link';
import Image from 'next/image';
import { UploadCloud, Zap, Users } from 'lucide-react';

// Helper component for "Coming Soon" tooltip
const ComingSoonTooltip = ({ children, tooltipText = "Coming soon!" }: { children: React.ReactNode, tooltipText?: string }) => {
  return (
    <div className="group relative inline-block cursor-default">
      {children}
      <span className="absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-black px-2 py-1 text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
        {tooltipText}
      </span>
    </div>
  );
};

interface FeatureCardProps {
  href: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  cardClassName?: string;
  iconClassName?: string;
  titleClassName?: string;
  descriptionClassName?: string;
}

function FeatureCard({ 
  href, 
  icon, 
  title, 
  description, 
  cardClassName,
  iconClassName,
  titleClassName,
  descriptionClassName 
}: FeatureCardProps) {
  return (
    <Link href={href} className={`p-4 rounded-lg shadow-lg flex flex-col items-center text-center ${cardClassName || 'bg-white/20'}`}>
      <div className={iconClassName || 'mb-2'}>{icon}</div>
      <h3 className={`font-semibold text-lg ${titleClassName || 'text-black'}`}>{title}</h3>
      <p className={`text-sm ${descriptionClassName || 'text-gray-800'}`}>{description}</p>
    </Link>
  );
}

export default function DashboardPage() {
  // TODO: Ensure all asset paths are correct and files exist in /public
  // Navbar background: /assets/dashboard-navbar.png
  // Gemstones: /assets/currencies/ruby.png, emerald.png, topaz.png, diamond.png
  // Character: /assets/characters/Jiaran.png

  // Approximate positions - these will likely need fine-tuning
  const navItemBaseStyle = "text-white font-semibold hover:opacity-80 transition-opacity text-base md:text-lg py-2 px-3 font-sans";
  const currencyAmountStyle = "text-white font-bold text-base ml-1 font-sans";

  return (
    <div 
      className="min-h-screen bg-cover bg-center text-white" 
      style={{ backgroundImage: "url('/assets/dashboard-background.png')" }}
    >
      {/* New Navbar with background image and interactive elements */}
      <nav 
        className="w-full fixed top-4 left-0 z-50 h-[120px] bg_bottom bg-no-repeat shadow-lg"
        style={{ backgroundImage: "url('/assets/dashboard-navbar.png')", backgroundSize: 'cover' }}
      >
        <div className="relative w-full h-full max-w-screen-2xl mx-auto px-4 md:px-6 lg:px-8 flex items-center justify-between">
          {/* Far Left: JiaranAI Logo */}
          <div style={{ position: 'absolute', left: '2%', top: '50%', transform: 'translateY(-50%)' }} className="flex items-center">
            <Image 
              src="/assets/logos/JiaranAI.png" 
              alt="JiaranAI Logo" 
              width={160} 
              height={160} 
              style={{ height: 'auto' }}
            />
          </div>

          {/* Navigation Links - Shifted right significantly */}
          <div className="flex items-center space-x-3 md:space-x-4" style={{ position: 'absolute', left: '22%', top: '50%', transform: 'translateY(-50%)' }}>
            <Link href="/dashboard" className={`${navItemBaseStyle} bg-purple-600/50 hover:bg-purple-600/70 rounded-md`}>
              Dashboard
            </Link>
            <ComingSoonTooltip>
              <span className={`${navItemBaseStyle} cursor-default`}>Daily Tournament</span>
            </ComingSoonTooltip>
            <ComingSoonTooltip>
              <span className={`${navItemBaseStyle} cursor-default`}>Personalized Tutor</span>
            </ComingSoonTooltip>
          </div>

          {/* Right side: User Stats - Restructured */}
          <div className="flex flex-col items-end space-y-1 md:space-y-2" style={{ position: 'absolute', right: '7%', top: '50%', transform: 'translateY(-50%)' }}>
            {/* Top Row: Currencies */}
            <div className="flex items-center space-x-2 md:space-x-4">
              <div className="flex items-center">
                <Image src="/assets/currencies/ruby.png" alt="Ruby" width={20} height={20} />
                <span className={currencyAmountStyle}>350</span>
              </div>
              <div className="flex items-center">
                <Image src="/assets/currencies/emerald.png" alt="Emerald" width={20} height={20} />
                <span className={currencyAmountStyle}>350</span>
              </div>
              <div className="flex items-center">
                <Image src="/assets/currencies/topaz.png" alt="Topaz" width={20} height={20} />
                <span className={currencyAmountStyle}>350</span>
              </div>
            </div>

            {/* Bottom Row: Level and XP Bar */}
            <div className="flex items-center space-x-2 md:space-x-3">
              <span className="text-white font-bold text-base md:text-lg font-sans">Lv.999</span>
              <div className="flex items-center bg-slate-700/70 rounded-full h-5 md:h-6 w-32 md:w-40 border border-slate-500/50 overflow-hidden p-0.5">
                <Image src="/assets/currencies/diamond.png" alt="XP Diamond" width={16} height={16} className="z-10 ml-0.5" />
                <div className="bg-white h-full rounded-sm ml-0.5" style={{ width: 'calc(75% - 16px)' }}></div>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content Area - Structure largely unchanged from previous step */}
      {/* Padding top adjusted to account for fixed navbar height */}
      <main className="pt-[140px] md:pt-[150px] px-4 flex flex-col items-center justify-center min-h-screen">
        <div className="w-full max-w-6xl mx-auto relative" style={{ minHeight: 'calc(100vh - 140px)' }}> {/* Ensure content area can fill space */}
          {/* Teacher Image - Adjusted position */}
          <div className="absolute" style={{ top: '13vh', left: '50%', transform: 'translateX(-40%)' }}>
            <Image 
              src="/assets/characters/Jiaran.png" 
              alt="Teacher Jiaran"
              width={300} 
              height={450} 
            />
          </div>

          {/* Speech Bubble */}
          <div 
            className="absolute bg-white/80 text-black p-4 rounded-lg shadow-xl" 
            style={{ top: '10vh', left: 'calc(50% + 100px)', width: '220px' }}
          >
            <p className="text-sm">Hi Ben,</p>
            <p className="text-sm">What do you want to learn today?</p>
            <div 
              style={{
                position: 'absolute',
                bottom: '50%',
                left: '-10px',
                transform: 'translateY(50%)',
                width: '0',
                height: '0',
                borderTop: '10px solid transparent',
                borderBottom: '10px solid transparent',
                borderRight: '10px solid rgba(255, 255, 255, 0.8)',
              }}
            />
          </div>

          {/* Feature Cards - Positioning might need review with new navbar and content flow */}
          <div className="absolute" style={{ top: '15vh', left: '10%', width: '250px'}}>
            <FeatureCard
              href="/upload"
              icon={<UploadCloud className="w-12 h-12 mb-2 text-black" />}
              title="Upload Content"
              description="Securely upload your lecture notes, PDFs, or text. We process it instantly."
              cardClassName="bg-purple-300/70 backdrop-blur-sm border border-purple-400/50"
              titleClassName="text-gray-900 font-bold"
              descriptionClassName="text-gray-700"
            />
          </div>
          <div className="absolute" style={{ top: '45vh', left: '10%', width: '250px'}}>
            <FeatureCard
              href="/classroom"
              icon={<Users className="w-12 h-12 mb-2 text-black" />}
              title="AI Classroom"
              description="Deepen your knowledge by discussing topics with our AI-powered virtual classmates."
              cardClassName="bg-purple-300/70 backdrop-blur-sm border border-purple-400/50"
              titleClassName="text-gray-900 font-bold"
              descriptionClassName="text-gray-700"
            />
          </div>
          <div className="absolute" style={{ top: '25vh', right: '5%', width: '250px'}}>
            <FeatureCard
              href="/swipe"
              icon={<Zap className="w-12 h-12 mb-2 text-black" />}
              title="Diagnostic Quizzes"
              description="Test your understanding with adaptive, swipe-style questions generated from your content."
              cardClassName="bg-purple-300/70 backdrop-blur-sm border border-purple-400/50"
              titleClassName="text-gray-900 font-bold"
              descriptionClassName="text-gray-700"
            />
          </div>
        </div>
      </main>

      {/* Updated Footer */}
      <footer className="w-full py-6 px-6 text-center bg-black/50 text-purple-200 text-xs md:text-sm font-sans">
        <p className="mb-2">
          Upload your course materials, get instant diagnostic quizzes, and engage in simulated classroom discussions to master any subject.
        </p>
        <p>
          © {new Date().getFullYear()} JiaranAI Learning Lab. All rights reserved.
        </p>
        <p className="mt-1">
          Created by Ben Anantachaisophon for CS109 final project.
        </p>
      </footer>
    </div>
  );
} 