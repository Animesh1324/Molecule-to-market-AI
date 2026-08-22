'use client';

import React, { useState } from 'react';
import { Sparkles, Send, X, Bot, User, Copy, Check, AlertTriangle } from 'lucide-react';
import { askCoPilot } from '../lib/api';
import { CoPilotTurn } from '../lib/types';
import MarkdownContent from './MarkdownContent';

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
  aiAnswered?: boolean;
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
      text: `Hello! I am your AI Pharma Brand Strategist for **${brandName}** (${moleculeName}). Ask me about positioning, objection handling, or launch strategy — every answer is grounded in this molecule's verified profile, evidence, regulatory status, and competitors on file.`,
      timestamp: 'Just now',
      aiAnswered: true,
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (!isOpen) return null;

  const quickPrompts = [
    `Draft a doctor detailer talk-track structure for ${brandName}`,
    `Suggest an objection-handling structure for hesitant prescribers`,
    `What should we validate before finalizing our positioning?`,
    `What evidence gaps should the medical team close first?`
  ];

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputText;
    if (!text.trim() || isTyping) return;

    const userMsg: Message = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: text.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const history: CoPilotTurn[] = messages.map((m) => ({ sender: m.sender, text: m.text }));
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsTyping(true);

    try {
      const result = await askCoPilot({
        molecule: moleculeName,
        brand_name: brandName,
        therapy_area: therapyArea,
        indication,
        question: text.trim(),
        history,
      });
      setMessages(prev => [...prev, {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: result.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        aiAnswered: result.ai_answered,
      }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: e instanceof Error ? e.message : 'The AI Co-Pilot request failed. Try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        aiAnswered: false,
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-lg bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-950/80">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-teal-500 flex items-center justify-center text-slate-900 dark:text-white shadow-md">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">AI Brand Strategist Co-Pilot</h3>
            <span className="text-[10px] text-teal-700 dark:text-teal-400 font-mono">Grounded in {moleculeName} verified data — never invented</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition"
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
            <div className="flex items-center space-x-1.5 text-[10px] text-slate-500 dark:text-slate-500 mb-1">
              {m.sender === 'user' ? (
                <>
                  <span>You</span>
                  <User className="w-3 h-3 text-slate-500 dark:text-slate-400" />
                </>
              ) : (
                <>
                  <Bot className="w-3 h-3 text-teal-700 dark:text-teal-400" />
                  <span className="text-teal-700 dark:text-teal-400 font-semibold">Pharma Brand AI</span>
                </>
              )}
              <span>• {m.timestamp}</span>
            </div>

            <div
              className={`p-3.5 rounded-2xl max-w-[90%] leading-relaxed relative group ${
                m.sender === 'user'
                  ? 'bg-brand-600 text-slate-900 dark:text-white rounded-br-none whitespace-pre-line'
                  : 'bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200 rounded-bl-none shadow-sm'
              }`}
            >
              {m.sender === 'ai' ? <MarkdownContent text={m.text} /> : m.text}

              {m.sender === 'ai' && (
                <button
                  onClick={() => handleCopy(m.id, m.text)}
                  className="absolute top-2 right-2 p-1 rounded bg-white dark:bg-slate-900/90 text-slate-500 dark:text-slate-400 hover:text-white opacity-0 group-hover:opacity-100 transition border border-slate-300 dark:border-slate-700"
                  title="Copy to clipboard"
                >
                  {copiedId === m.id ? (
                    <Check className="w-3 h-3 text-emerald-700 dark:text-emerald-400" />
                  ) : (
                    <Copy className="w-3 h-3" />
                  )}
                </button>
              )}
            </div>
            {m.sender === 'ai' && m.aiAnswered === false && (
              <span className="mt-1 flex items-center gap-1 text-[10px] text-amber-600 dark:text-amber-400">
                <AlertTriangle className="w-3 h-3" /> Not AI-generated — see message for why
              </span>
            )}
          </div>
        ))}

        {isTyping && (
          <div className="flex items-center space-x-2 text-slate-500 dark:text-slate-400 text-xs py-2">
            <Bot className="w-4 h-4 text-teal-700 dark:text-teal-400 animate-spin" />
            <span>Drafting a grounded response...</span>
          </div>
        )}
      </div>

      {/* Quick Prompts */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 overflow-x-auto">
        <div className="flex items-center space-x-2 min-w-max">
          {quickPrompts.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(p)}
              disabled={isTyping}
              className="px-2.5 py-1 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 text-[11px] whitespace-nowrap transition"
            >
              💬 {p.slice(0, 32)}...
            </button>
          ))}
        </div>
      </div>

      {/* Input Box */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
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
            className="flex-1 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl px-3.5 py-2 text-xs text-slate-900 dark:text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isTyping}
            className="p-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-slate-900 dark:text-white transition disabled:opacity-40"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
