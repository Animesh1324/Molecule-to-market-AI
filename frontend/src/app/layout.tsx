import type { Metadata } from 'next';
import '../styles/globals.css';
import MLRComplianceBanner from '../components/MLRComplianceBanner';
import { ThemeProvider } from '../components/ThemeProvider';

export const metadata: Metadata = {
  title: 'Pharma BrandPlan AI — Molecule to Commercial Strategy',
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
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP }} />
      </head>
      <body className="bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 min-h-screen flex flex-col font-sans transition-colors">
        <ThemeProvider>
          <MLRComplianceBanner />
          <main className="flex-1 flex flex-col">{children}</main>
          <footer className="bg-slate-50 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800/80 py-6 px-6 text-center text-xs text-slate-500 dark:text-slate-500 dark:text-slate-500">
            <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="font-semibold text-slate-600 dark:text-slate-400">Pharma BrandPlan AI</span> — Evidence-Grounded Pharma Commercialization Engine
              </div>
              <div>
                Built for Brand Managers, Medical Affairs &amp; Launch Teams | Review-Required Draft Outputs
              </div>
            </div>
          </footer>
        </ThemeProvider>
      </body>
    </html>
  );
}
