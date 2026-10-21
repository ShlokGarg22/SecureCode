"use client";

import React, { useState } from "react";
import { Copy, Check, Split, AlignLeft, ShieldCheck, Bug } from "lucide-react";

export default function CodeDiffViewer({ originalCode, correctedCode, diffUnified, filePath, lineNumber }) {
  const [viewMode, setViewMode] = useState("split"); // "split" or "unified"
  const [copied, setCopied] = useState(false);

  const copyToClipboard = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const origLines = (originalCode || "").trim().split("\n");
  const fixedLines = (correctedCode || "").trim().split("\n");
  const maxLines = Math.max(origLines.length, fixedLines.length);

  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
      {/* Diff Controls Header */}
      <div className="bg-slate-50 px-4 py-2.5 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center space-x-2 font-mono text-slate-700">
          <span className="font-semibold text-slate-900">{filePath}</span>
          <span className="text-slate-400">•</span>
          <span className="text-slate-500">around Line {lineNumber}</span>
        </div>

        <div className="flex items-center space-x-2">
          {/* Toggle Split / Unified */}
          <div className="flex items-center bg-slate-200/80 p-0.5 rounded-lg border border-slate-300">
            <button
              onClick={() => setViewMode("split")}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                viewMode === "split"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Split className="w-3.5 h-3.5" />
              <span>Side-by-Side</span>
            </button>

            <button
              onClick={() => setViewMode("unified")}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                viewMode === "unified"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <AlignLeft className="w-3.5 h-3.5" />
              <span>Unified Diff</span>
            </button>
          </div>

          {/* Copy Patch */}
          <button
            onClick={() => copyToClipboard(correctedCode || diffUnified)}
            className="flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 font-medium transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
            <span>{copied ? "Copied!" : "Copy Fix"}</span>
          </button>
        </div>
      </div>

      {/* SIDE-BY-SIDE SPLIT VIEW */}
      {viewMode === "split" && (
        <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-200 font-mono text-xs">
          {/* Left: Original Vulnerable Code */}
          <div className="bg-rose-50/40">
            <div className="px-3 py-1.5 bg-rose-100/60 border-b border-rose-200 flex items-center justify-between text-[11px] font-semibold text-rose-800">
              <span className="flex items-center space-x-1">
                <Bug className="w-3 h-3 text-rose-600" />
                <span>Original (Vulnerable Code)</span>
              </span>
              <span className="text-rose-500 font-normal">Original snippet</span>
            </div>
            <div className="p-3 overflow-x-auto space-y-0.5 leading-relaxed">
              {origLines.map((line, idx) => (
                <div key={idx} className="flex items-start text-rose-900 hover:bg-rose-100/50 py-0.5 px-1 rounded">
                  <span className="w-6 text-rose-400 select-none text-right pr-2 text-[10px]">
                    {lineNumber ? lineNumber + idx : idx + 1}
                  </span>
                  <span className="text-rose-600 font-bold select-none pr-2">-</span>
                  <span className="whitespace-pre flex-1">{line || " "}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right: AI Remediated Secure Fix */}
          <div className="bg-emerald-50/40">
            <div className="px-3 py-1.5 bg-emerald-100/60 border-b border-emerald-200 flex items-center justify-between text-[11px] font-semibold text-emerald-800">
              <span className="flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3 text-emerald-600" />
                <span>AI Suggested Remediation</span>
              </span>
              <span className="text-emerald-600 font-normal">Safe drop-in fix</span>
            </div>
            <div className="p-3 overflow-x-auto space-y-0.5 leading-relaxed">
              {fixedLines.map((line, idx) => (
                <div key={idx} className="flex items-start text-emerald-950 hover:bg-emerald-100/50 py-0.5 px-1 rounded">
                  <span className="w-6 text-emerald-500 select-none text-right pr-2 text-[10px]">
                    {lineNumber ? lineNumber + idx : idx + 1}
                  </span>
                  <span className="text-emerald-600 font-bold select-none pr-2">+</span>
                  <span className="whitespace-pre flex-1">{line || " "}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* UNIFIED DIFF VIEW */}
      {viewMode === "unified" && (
        <div className="bg-slate-900 p-4 font-mono text-xs overflow-x-auto text-slate-100 leading-relaxed">
          <div className="text-slate-400 text-[11px] pb-2 border-b border-slate-800 mb-2">
            --- a/{filePath} (Vulnerable)<br />
            +++ b/{filePath} (Remediated)
          </div>
          {diffUnified ? (
            diffUnified.split("\n").map((dline, i) => {
              const isDel = dline.startsWith("-");
              const isAdd = dline.startsWith("+");
              const isHunk = dline.startsWith("@");
              return (
                <div
                  key={i}
                  className={`px-1 rounded ${
                    isDel
                      ? "bg-rose-950/60 text-rose-300 font-medium"
                      : isAdd
                      ? "bg-emerald-950/60 text-emerald-300 font-medium"
                      : isHunk
                      ? "text-cyan-400 font-semibold"
                      : "text-slate-300"
                  }`}
                >
                  {dline}
                </div>
              );
            })
          ) : (
            <pre className="text-slate-300 whitespace-pre">{correctedCode}</pre>
          )}
        </div>
      )}
    </div>
  );
}
