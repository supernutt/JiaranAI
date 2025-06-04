import Link from 'next/link';
import Image from 'next/image';

// TODO: Ensure "Gotham Bold" and "Gotham Extra Bold" fonts are loaded in the project.
// You might need to import them in globals.css and add them to tailwind.config.js theme.fontFamily.
// For now, using font-bold and a generic sans-serif.
// Example for tailwind.config.js:
// fontFamily: {
//   sans: [\'Gotham\', \'sans-serif\'], // Default sans-serif
//   gothamBold: [\'Gotham Bold\', \'sans-serif\'],
//   gothamExtraBold: [\'Gotham Extra Bold\', \'sans-serif\'],
// }
// Then you could use classes like `font-gothamBold` or `font-gothamExtraBold`.

export default function LandingPage() {
  return (
    // TODO: Implement the background style as shown in the image.
    // This might involve a CSS gradient or a background image.
    // Example: style={{ backgroundImage: 'url("/path/to/your/background.jpg")' }}
    // Or using Tailwind classes if you define the gradient/image in tailwind.config.js
    <div 
      className="min-h-screen flex flex-col items-center justify-center p-4 text-white bg-cover bg-center"
      style={{ backgroundImage: 'url("/assets/landing-background.png")' }} // Assumes you place the image at frontend/public/assets/landing-background.png
    >
      {/* Placeholder for the complex background from the image */}

      <main className="flex flex-col items-center justify-center text-center space-y-4 flex-grow">
        {/* Logo container */}
        <div className="flex items-center justify-center">
          <Image
            src="/assets/logos/JiaranAI.png" // Assumed path, confirm or update
            alt="JiaranAI Logo"
            width={240} // Increased size from 200
            height={240} // Increased size from 200
            style={{ height: 'auto' }} // Maintain aspect ratio if width is constrained by CSS or parent
          />
        </div>

        {/* Headline Text */}
        {/* "We Craft. You Learn." uses Gotham Bold (font-bold) */}
        {/* "JiaranAI" (if text) uses Gotham Bold (font-bold) */}
        <h1 className="text-7xl md:text-8xl font-bold leading-tight">
          {/* This is a placeholder for JiaranAI text if it's part of the logo image, or add text here */}
          {/* <span className="block mb-2 text-4xl font-bold">JiaranAI</span> */}
          We <span style={{ color: '#96DCFD' }}>Craft</span><span style={{ color: 'white' }}>.</span>
          <br />
          You <span style={{ color: '#EFC900' }}>Learn</span><span style={{ color: 'white' }}>.</span>
        </h1>
        
        {/* Get Started Button */}
        <Link
          href="/dashboard"
          className="bg-[#7851A9] text-white font-bold py-3 px-10 rounded-lg text-xl hover:bg-[#6A409A] transition-colors shadow-lg"
        >
          Get Started
        </Link>
      </main>

      {/* Optional: Footer if needed on the landing page */}
      {/* <footer className="w-full p-4 text-center text-sm text-gray-300">
        <p>© {new Date().getFullYear()} JiaranAI. All rights reserved.</p>
      </footer> */}
    </div>
  );
} 