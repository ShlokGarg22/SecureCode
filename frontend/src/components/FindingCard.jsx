"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, Sparkles, ShieldAlert, AlertTriangle, Bug, Code, ArrowRight } from "lucide-react";
import CodeDiffViewer from "./CodeDiffViewer";

export default function FindingCard({ finding }) {
  const [isOpen, setIsOpen] = useState(true);

  const getSeverityStyle = (severity) => {
    switch (severity?.toLowerCase()) {
      case "critical":
        return "bg-rose-100 text-rose-800 border-rose-300";
      case "high":
        return "bg-orange-100 text-orange-800 border-orange-300";
      case "medium":
        return "bg-amber-100 text-amber-800 border-amber-300";
      case "low":
        return "bg-blue-100 text-blue-800 border-blue-300";
      default:
        return "bg-slate-100 text-slate-700 border-slate-300";
    }
  };

  const ai = finding.ai_explanation;

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs hover:border-slate-300 transition-all">
      {/* Header Bar */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="p-4 cursor-pointer flex items-center justify-between hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center space-x-3 overflow-hidden">
          {/* Severity Badge */}
          <span className={`text-[11px] px-2.5 py-1 rounded-md font-bold border uppercase tracking-wider shrink-0 ${getSeverityStyle(finding.severity)}`}>
            {finding.severity}
          </span>

          {/* Title & File Path */}
          <div className="truncate">
            <h4 className="text-sm font-bold text-slate-900 truncate">{finding.title}</h4>
            <div className="flex items-center space-x-2 text-xs text-slate-500 mt-0.5">
              <span className="font-mono text-blue-600 font-semibold">{finding.file_path}:{finding.line_number}</span>
              <span>•</span>
              <span className="text-slate-500">{finding.rule_id}</span>
              <span>•</span>
              <span className="px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 font-mono text-[10px] border border-slate-200">
                {finding.tool}
              </span>
            </div>
          </div>
        </div>

        {/* Toggle chevron */}
        <div className="text-slate-400 shrink-0 ml-3">
          {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </div>
      </div>

      {/* Expanded Content */}
      {isOpen && (
        <div className="p-4 pt-2 border-t border-slate-100 space-y-4 text-xs">
          {/* Description & Impact */}
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
            <p className="text-slate-800 leading-relaxed font-medium">{finding.description}</p>
            {finding.impact && (
              <p className="text-slate-600 mt-1.5 leading-relaxed">
                <span className="font-bold text-slate-700">Security Impact: </span>
                {finding.impact}
              </p>
            )}
          </div>

          {/* AI Attack Vector & Exploit Details */}
          {ai?.attack_scenario && (
            <div className="bg-purple-50 p-3.5 rounded-lg border border-purple-200">
              <div className="flex items-center space-x-1.5 text-purple-900 font-bold mb-1">
                <Sparkles className="w-4 h-4 text-purple-600" />
                <span>Realistic Attack Exploit Scenario</span>
              </div>
              <p className="text-purple-950 leading-relaxed">{ai.attack_scenario}</p>
            </div>
          )}

          {/* Recommended Remediation Guidance */}
          {ai?.recommended_fix && (
            <div>
              <h5 className="font-bold text-slate-900 mb-1">Recommended Remediation:</h5>
              <p className="text-slate-700 leading-relaxed">{ai.recommended_fix}</p>
            </div>
          )}

          {/* Code Diff Block (Side-by-Side Comparison) */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h5 className="font-bold text-slate-900 flex items-center space-x-1.5">
                <Code className="w-4 h-4 text-blue-600" />
                <span>Proposed Code Changes (Side-by-Side Comparison)</span>
              </h5>
              <span className="text-[11px] text-slate-500 font-mono">
                {ai?.provider || "AI Engine"} • {ai?.model || "Standard"}
              </span>
            </div>

            <CodeDiffViewer
              originalCode={ai?.original_code || finding.evidence_snippet}
              correctedCode={ai?.corrected_code}
              diffUnified={ai?.diff_unified}
              filePath={finding.file_path}
              lineNumber={finding.line_number}
            />
          </div>

          {/* Verification note */}
          {ai?.uncertainty_note && (
            <p className="text-[11px] text-slate-500 italic bg-slate-50 px-3 py-1.5 rounded border border-slate-200">
              Note: {ai.uncertainty_note}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
