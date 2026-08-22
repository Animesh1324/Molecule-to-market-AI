import type { Metadata } from 'next';
import '../styles/globals.css';
import MLRComplianceBanner from '../components/MLRComplianceBanner';
import { ThemeProvider } from '../components/ThemeProvider';
import { CurrencyProvider } from '../components/CurrencyProvider';

export const metadata: Metadata = {
  title: 'Molecule to Market AI — Molecule to Commercial Strategy',
  description: 'Enterprise pharmaceutical brand planning, clinical evidence synthesis, and commercial launch engine.',
};

// Applied before first paint so a light-theme user never sees a dark flash.
const THEME_BOOTSTRAP = `
(function () {
  try {
    var stored = localStorage.getItem('brandplan-theme');
    var light = stored === 'light' ||
      (!stored && window.matchMedia('(prefers-color-scheme: light)').matches);
    document.documentElement.classList.toggle('dark', !light);
    document.documentElement.style.colorScheme = light ? 'light' : 'dark';
  } catch (e) {
    document.documentElement.classList.add('dark');
  }
})();
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        {/* Same families as animesh-portfolio: Inter for body, DM Serif
            Display for headings. Preconnect so the serif is not a late swap. */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Playfair+Display:ital,wght@0,600;0,700;1,600&family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP }} />
      </head>
      <body className="bg-white dark:bg-navy-950 text-navy-900 dark:text-navy-100 min-h-screen flex flex-col font-sans transition-colors">
        <ThemeProvider>
        <CurrencyProvider>
          <MLRComplianceBanner />
          <main className="flex-1 flex flex-col">{children}</main>
          <footer className="bg-slate-50 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800/80 py-6 px-6 text-center text-xs text-slate-500 dark:text-slate-500 dark:text-slate-500">
            <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="font-semibold text-slate-600 dark:text-slate-400">Molecule to Market AI</span> — Evidence-Grounded Pharma Commercialization Engine
              </div>
              <div>
                Built for Brand Managers, Medical Affairs &amp; Launch Teams | Review-Required Draft Outputs
              </div>
              <div className="text-slate-400 dark:text-slate-600 flex items-center gap-1.5 flex-wrap justify-center sm:justify-end">
                <span>Developed by Animesh Mishra</span>
                <span>·</span>
                <a href="mailto:animesh.pm17@iihmr.in" className="hover:text-slate-600 dark:hover:text-slate-400 underline underline-offset-2">
                  animesh.pm17@iihmr.in
                </a>
                <span>·</span>
                <a href="https://www.linkedin.com/in/animeshmishra-pm17" target="_blank" rel="noreferrer" className="hover:text-slate-600 dark:hover:text-slate-400 underline underline-offset-2">
                  LinkedIn
                </a>
              </div>
            </div>
          </footer>
        </CurrencyProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
