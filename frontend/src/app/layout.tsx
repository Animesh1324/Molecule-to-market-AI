import type { Metadata } from 'next';
import '../styles/globals.css';
import MLRComplianceBanner from '../components/MLRComplianceBanner';

export const metadata: Metadata = {
  title: 'Pharma BrandPlan AI — Molecule to Commercial Strategy',
  description: 'Enterprise pharmaceutical brand planning, clinical evidence synthesis, and commercial launch engine.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col font-sans">
        <MLRComplianceBanner />
        <main className="flex-1 flex flex-col">
          {children}
        </main>
        <footer className="bg-slate-950 border-t border-slate-800/80 py-6 px-6 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="font-semibold text-slate-400">Pharma BrandPlan AI</span> — Evidence-Grounded Pharma Commercialization Engine
            </div>
            <div>
              Built for Brand Managers, Medical Affairs & Launch Teams | Review-Required Draft Outputs
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
