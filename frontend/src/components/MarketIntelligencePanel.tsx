'use client';

/**
 * Measured market view for a molecule, read from ingested secondary data
 * (IQVIA/IMS TSA, PharmaTrac, AWACS).
 *
 * Every number here is an audited fact from a file the team supplied, so the
 * panel always states its period and source file rather than presenting the
 * figures as the application's own. When no extract covers the molecule the
 * panel renders an explicit empty state — it never falls back to an estimate.
 */

import { Building2, Database, Layers, TrendingDown, TrendingUp } from 'lucide-react';
import type { ClassRival, CompanyShare, CompetitorProfile, MarketSummary } from '@/lib/types';

interface Props {
  summary: MarketSummary;
  brands: CompetitorProfile[];
  companies: CompanyShare[];
  classRivals: ClassRival[];
  moleculeName: string;
}

/** Indian audit extracts report value in crore; show that natively. */
function formatValue(value?: number | null, unit?: string | null): string {
  if (value === null || value === undefined) return '—';
  const rounded = value >= 100 ? value.toFixed(0) : value.toFixed(2);
  return `${rounded} ${unit || ''}`.trim();
}

function GrowthBadge({ value }: { value?: number | null }) {
  if (value === null || value === undefined) {
    return <span className="text-slate-400 dark:text-slate-600">—</span>;
  }
  const positive = value >= 0;
  const Icon = positive ? TrendingUp : TrendingDown;
  return (
    <span
      className={`inline-flex items-center gap-1 font-mono text-xs font-semibold ${
        positive ? 'text-emerald-700 dark:text-emerald-400' : 'text-rose-700 dark:text-rose-400'
      }`}
    >
      <Icon className="w-3 h-3" aria-hidden />
      {positive ? '+' : ''}
      {value.toFixed(1)}%
    </span>
  );
}

export default function MarketIntelligencePanel({
  summary,
  brands,
  companies,
  classRivals,
  moleculeName,
}: Props) {
  if (!summary?.has_data) {
    return (
      <div className="p-6 rounded-2xl border border-amber-400/60 bg-amber-50 dark:bg-amber-950/30 space-y-2">
        <div className="flex items-center gap-2 text-amber-900 dark:text-amber-200 font-bold text-sm">
          <Database className="w-4 h-4" aria-hidden />
          No market extract covers {moleculeName}
        </div>
        <p className="text-xs text-amber-800 dark:text-amber-300/90 leading-relaxed">
          Brand-level competition, company share, and market size come from a licensed audit
          extract. Upload an IQVIA/IMS, PharmaTrac, or AWACS file under{' '}
          <strong>Secondary Data</strong> and this panel fills in automatically — no other setup.
        </p>
      </div>
    );
  }

  const marketBrands = brands.filter((b) => b.data_source === 'secondary_market');
  const topShare = marketBrands[0]?.market_share_percentage ?? 0;

  return (
    <div className="space-y-5">
      {/* Headline measures */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Market size
          </span>
          <div className="text-xl font-extrabold text-slate-900 dark:text-white mt-1 tabular-nums">
            {formatValue(summary.market_size, summary.value_unit)}
          </div>
          <div className="mt-1">
            <GrowthBadge value={summary.market_growth_percent} />
          </div>
        </div>
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Brands competing
          </span>
          <div className="text-xl font-extrabold text-slate-900 dark:text-white mt-1 tabular-nums">
            {summary.total_brands}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            across {summary.total_companies} companies
          </div>
        </div>
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Leader share
          </span>
          <div className="text-xl font-extrabold text-slate-900 dark:text-white mt-1 tabular-nums">
            {topShare ? `${topShare.toFixed(1)}%` : '—'}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 truncate">
            {marketBrands[0]?.brand_name || '—'}
          </div>
        </div>
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Period · market
          </span>
          <div className="text-sm font-bold text-slate-900 dark:text-white mt-1 font-mono">
            {summary.period || '—'}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            {summary.market || '—'}
          </div>
        </div>
      </div>

      {/* Brand leaderboard. Wide table scrolls inside its own box so the page
          body never scrolls sideways on a narrow screen. */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4 text-brand-600 dark:text-brand-400" aria-hidden />
            Brands in market — {moleculeName}
          </h3>
          <span className="text-[10px] font-mono text-slate-500 dark:text-slate-400">
            showing {marketBrands.length} of {summary.total_brands}
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs min-w-[720px]">
            <thead>
              <tr className="text-left text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                <th className="px-4 py-2.5 font-semibold">#</th>
                <th className="px-4 py-2.5 font-semibold">Brand</th>
                <th className="px-4 py-2.5 font-semibold">Company</th>
                <th className="px-4 py-2.5 font-semibold">Molecule as sold</th>
                <th className="px-4 py-2.5 font-semibold text-right whitespace-nowrap">Value</th>
                <th className="px-4 py-2.5 font-semibold text-right">Share</th>
                <th className="px-4 py-2.5 font-semibold text-right whitespace-nowrap">Growth</th>
              </tr>
            </thead>
            <tbody>
              {marketBrands.map((brand, index) => (
                <tr
                  key={`${brand.brand_name}-${brand.company}-${index}`}
                  className="border-b border-slate-100 dark:border-slate-800/60 hover:bg-slate-50 dark:hover:bg-slate-800/40"
                >
                  <td className="px-4 py-2.5 font-mono text-slate-400 dark:text-slate-600 tabular-nums">
                    {index + 1}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="font-bold text-slate-900 dark:text-white">{brand.brand_name}</span>
                    {brand.is_combination && (
                      <span className="ml-2 px-1.5 py-0.5 rounded text-[9px] font-mono uppercase bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                        combo
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-slate-700 dark:text-slate-300">
                    {brand.company}
                    {brand.ownership && (
                      <span className="ml-1.5 text-[9px] font-mono text-slate-400 dark:text-slate-600">
                        {brand.ownership}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-slate-500 dark:text-slate-400 max-w-[220px] truncate" title={brand.molecule}>
                    {brand.molecule}
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono tabular-nums text-slate-800 dark:text-slate-100 whitespace-nowrap">
                    {formatValue(brand.market_value, brand.value_unit)}
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-14 h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden hidden sm:block">
                        <div
                          className="h-full bg-brand-500 dark:bg-brand-400"
                          style={{ width: `${Math.min(100, brand.market_share_percentage)}%` }}
                        />
                      </div>
                      <span className="font-mono tabular-nums text-slate-800 dark:text-slate-100">
                        {brand.market_share_percentage.toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <GrowthBadge value={brand.market_growth_percent} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Corporate share */}
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <Building2 className="w-4 h-4 text-brand-600 dark:text-brand-400" aria-hidden />
              Corporate share
            </h3>
          </div>
          <div className="p-4 space-y-2.5">
            {companies.slice(0, 8).map((company) => (
              <div key={company.company} className="space-y-1">
                <div className="flex items-center justify-between gap-3 text-xs">
                  <span className="font-semibold text-slate-800 dark:text-slate-100 truncate">
                    {company.company}
                    <span className="ml-1.5 text-[10px] font-normal text-slate-400 dark:text-slate-600">
                      {company.brand_count} brand{company.brand_count === 1 ? '' : 's'}
                    </span>
                  </span>
                  <span className="font-mono tabular-nums text-slate-700 dark:text-slate-300 shrink-0">
                    {company.market_share_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-brand-500 dark:bg-brand-400"
                    style={{ width: `${Math.min(100, company.market_share_percent)}%` }}
                  />
                </div>
              </div>
            ))}
            {companies.length === 0 && (
              <p className="text-xs text-slate-500 dark:text-slate-400">
                The extract does not carry a company column for this molecule.
              </p>
            )}
          </div>
        </div>

        {/* Class rivals */}
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider">
              Class rivals
            </h3>
            {summary.therapy_group && (
              <p className="text-[10px] font-mono text-slate-500 dark:text-slate-400 mt-1 truncate">
                {summary.therapy_group}
                {summary.group_value
                  ? ` · ${formatValue(summary.group_value, summary.value_unit)}`
                  : ''}
              </p>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <tbody>
                {classRivals.slice(0, 10).map((rival, index) => (
                  <tr
                    key={`${rival.molecule_key}-${index}`}
                    className="border-b border-slate-100 dark:border-slate-800/60 last:border-0"
                  >
                    <td className="px-4 py-2 text-slate-800 dark:text-slate-100 max-w-[200px] truncate" title={rival.molecule_desc}>
                      {rival.molecule_desc}
                      <span className="ml-1.5 text-[10px] text-slate-400 dark:text-slate-600">
                        {rival.brand_count} brands
                      </span>
                    </td>
                    <td className="px-3 py-2 text-right font-mono tabular-nums text-slate-700 dark:text-slate-300 whitespace-nowrap">
                      {formatValue(rival.value_latest, summary.value_unit)}
                    </td>
                    <td className="px-4 py-2 text-right whitespace-nowrap">
                      <GrowthBadge value={rival.growth_percent} />
                    </td>
                  </tr>
                ))}
                {classRivals.length === 0 && (
                  <tr>
                    <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">
                      No therapeutic group is recorded for this molecule in the extract.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Provenance. A share figure without its source file cannot be reviewed. */}
      {summary.source_files.length > 0 && (
        <p className="text-[10px] font-mono text-slate-500 dark:text-slate-500 flex items-start gap-1.5">
          <Database className="w-3 h-3 mt-0.5 shrink-0" aria-hidden />
          <span>
            Source: {summary.source_files.join(', ')} · {summary.period} · measured sales, not an
            estimate. Positioning and claims are not derived from this file.
          </span>
        </p>
      )}
    </div>
  );
}
