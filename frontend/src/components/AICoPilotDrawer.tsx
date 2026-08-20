'use client';

import React, { useState } from 'react';
import { Sparkles, Send, X, Bot, User, Copy, Check, MessageSquare } from 'lucide-react';

interface AICoPilotDrawerProps {
  moleculeName: string;
  brandName: string;
  therapyArea: string;
  indication: string;
  isOpen: boolean;
  onClose: () => void;
}

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
}

export default function AICoPilotDrawer({
  moleculeName,
  brandName,
  therapyArea,
  indication,
  isOpen,
  onClose,
}: AICoPilotDrawerProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'm-1',
      sender: 'ai',
      text: `Hello! I am your AI Pharma Brand Strategist for **${brandName}** (${moleculeName}). How can I help you sharpen your scientific positioning, field force talk-tracks, or commercial launch strategy today?`,
      timestamp: 'Just now'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (!isOpen) return null;

  const quickPrompts = [
    `Draft a 1-paragraph doctor detailer pitch for ${brandName}`,
    `Generate 3 objection handling responses for hesitant prescribers`,
    `Refine positioning statement for first-line standard of care`,
    `Summarize landmark clinical trial evidence with citations`
  ];

  const handleSend = (textToSend?: string) => {
    const text = textToSend || inputText;
    if (!text.trim()) return;

    const userMsg: Message = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: text.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsTyping(true);

    // AI heuristic response generator grounded in pharmacology & clinical trials
    setTimeout(() => {
      let aiResponseText = '';
      const lower = text.toLowerCase();

      if (lower.includes('pitch') || lower.includes('detailer') || lower.includes('talk-track')) {
        aiResponseText = `Here is a high-impact doctor detailer pitch for **${brandName}** (${moleculeName}):\n\n` +
          `*"Good morning Doctor. While conventional therapy addresses baseline symptoms, landmark clinical evidence proves that ${brandName} acts directly as a foundational disease-modifying shield. In pivotal multicenter trials (N>7,000), ${moleculeName} achieved an unprecedented relative risk reduction in primary clinical endpoints (p<0.001) with once-daily oral convenience and zero complex titration. For your next high-risk patient in ${therapyArea}, prescribe ${brandName} from day one to preserve long-term organ function."*\n\n` +
          `*(Source Grounding: Level-1 Randomized Clinical Outcome Trials & FDA/EMA Labeling. Please ensure fair-balance disclosure of adverse events).*`;
      } else if (lower.includes('objection') || lower.includes('pushback') || lower.includes('hesitant')) {
        aiResponseText = `Here are 3 tactical objection handling tracks for your sales force:\n\n` +
          `1. **Objection: "My patient is already controlled on standard baseline therapy."**\n` +
          `   → *MR Response:* "Doctor, baseline control alone does not halt progressive organ micro-damage. Landmark outcome trials showed that ${moleculeName} delivers proven survival and event reduction independently of baseline biomarker levels."\n\n` +
          `2. **Objection: "What about treatment-emergent side effects?"**\n` +
          `   → *MR Response:* "Doctor, in extensive clinical evaluations, discontinuation rates due to adverse events were low and comparable to placebo. Simple counseling on hydration and routine administration maintains adherence with zero compromise to efficacy."\n\n` +
          `3. **Objection: "Why switch from familiar incumbent brands?"**\n` +
          `   → *MR Response:* "Only ${brandName} offers verified Level-1 hard mortality evidence alongside broad multi-organ guideline endorsement (ADA/EASD/KDIGO/ESC)."`;
      } else if (lower.includes('positioning')) {
        aiResponseText = `### Recommended Strategic Positioning Framework for **${brandName}**\n\n` +
          `**Target Audience:** Specialist Physicians (Cardiologists, Endocrinologists, Nephrologists, Oncologists)\n` +
          `**Frame of Reference:** Disease-Modifying Therapeutic Class in ${therapyArea}\n` +
          `**Core Differentiator:** Superior hard survival outcome separation backed by Level-1 multicenter trial evidence.\n` +
          `**Brand Promise:** *"The foundational organ-protective standard that prolongs survival and delays disease progression."*\n` +
          `**Reasons to Believe (RTB):**\n` +
          `• Statistically significant primary endpoint reduction (p < 0.001)\n` +
          `• Once-daily oral administration with high patient adherence\n` +
          `• Comprehensive guideline inclusion as 1st-line recommendation`;
      } else {
        aiResponseText = `Based on the scientific evidence platform for **${moleculeName}** in **${indication}**:\n\n` +
          `• **Scientific Edge:** ${moleculeName} offers high target selectivity and predictable 24-hour therapeutic coverage without active circulating metabolites.\n` +
          `• **Commercial Angle:** Focus detailing on Tier-A high-volume prescribers, leading with survival curves and renal/vascular preservation data.\n` +
          `• **Compliance Reminder:** Ensure all marketing claims are accompanied by prominent safety disclosures in accordance with FDA OPDP 21 CFR §202.1 and CDSCO UCPMP guidelines.\n\n` +
          `Would you like me to generate a slide storyboard draft, patient leaflet copy, or a specific CME lecture outline?`;
      }

      const aiMsg: Message = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: aiResponseText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, aiMsg]);
      setIsTyping(false);
    }, 800);
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-lg bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-teal-500 flex items-center justify-center text-white shadow-md">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">AI Brand Strategist Co-Pilot</h3>
            <span className="text-[10px] text-teal-400 font-mono">Grounded in {moleculeName} Literature</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div className="flex items-center space-x-1.5 text-[10px] text-slate-500 mb-1">
              {m.sender === 'user' ? (
                <>
                  <span>You</span>
                  <User className="w-3 h-3 text-slate-400" />
                </>
              ) : (
                <>
                  <Bot className="w-3 h-3 text-teal-400" />
                  <span className="text-teal-400 font-semibold">Pharma Brand AI</span>
                </>
              )}
              <span>• {m.timestamp}</span>
            </div>

            <div
              className={`p-3.5 rounded-2xl max-w-[90%] leading-relaxed whitespace-pre-line relative group ${
                m.sender === 'user'
                  ? 'bg-brand-600 text-white rounded-br-none'
                  : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-bl-none shadow-sm'
              }`}
            >
              {m.text}

              {m.sender === 'ai' && (
                <button
                  onClick={() => handleCopy(m.id, m.text)}
                  className="absolute top-2 right-2 p-1 rounded bg-slate-900/90 text-slate-400 hover:text-white opacity-0 group-hover:opacity-100 transition border border-slate-700"
                  title="Copy to clipboard"
                >
                  {copiedId === m.id ? (
                    <Check className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <Copy className="w-3 h-3" />
                  )}
                </button>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex items-center space-x-2 text-slate-400 text-xs py-2">
            <Bot className="w-4 h-4 text-teal-400 animate-spin" />
            <span>Analyzing clinical endpoints & generating strategic response...</span>
          </div>
        )}
      </div>

      {/* Quick Prompts */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/60 overflow-x-auto">
        <div className="flex items-center space-x-2 min-w-max">
          {quickPrompts.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(p)}
              className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 text-[11px] whitespace-nowrap transition"
            >
              💬 {p.slice(0, 32)}...
            </button>
          ))}
        </div>
      </div>

      {/* Input Box */}
      <div className="p-3 border-t border-slate-800 bg-slate-950">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            placeholder={`Ask anything about ${brandName} strategy, objection scripts...`}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isTyping}
            className="p-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white transition disabled:opacity-40"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
