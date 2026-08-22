'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';

/**
 * Renders `content_markdown`-style text as actual headings, bold, and lists.
 *
 * Before this, sections were dumped as a raw string with `whitespace-pre-line`
 * — the `###` and `**` markers showed up as literal characters instead of
 * being parsed, which is worse than plain prose, not better.
 */
export default function MarkdownContent({ text }: { text: string }) {
  return (
    <ReactMarkdown
      components={{
        h3: ({ children }) => (
          <h3 className="text-sm font-bold text-slate-900 dark:text-white mt-3 mb-1.5 first:mt-0">{children}</h3>
        ),
        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
        ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-2">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-2">{children}</ol>,
        li: ({ children }) => <li className="leading-relaxed">{children}</li>,
        strong: ({ children }) => <strong className="font-semibold text-slate-800 dark:text-slate-100">{children}</strong>,
        em: ({ children }) => <em className="italic">{children}</em>,
      }}
    >
      {text}
    </ReactMarkdown>
  );
}
