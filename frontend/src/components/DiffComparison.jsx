"use client";

import React, { useState, useEffect } from "react";
import { GitCompare, CheckCircle2, AlertCircle, RefreshCw, ArrowRight, ShieldCheck, AlertTriangle } from "lucide-react";
import { getScanHistory, compareScans } from "@/lib/api";
import FindingCard from "./FindingCard";

export default function DiffComparison() {
  const [scans, setScans] = useState([]);
  const [baseScanId, setBaseScanId] = useState("");
  const [targetScanId, setTargetScanId] = useState("");
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeSubTab, setActiveSubTab] = useState("fixed");

  useEffect(() => {
    async function loadScans() {
      try {
        const list = await getScanHistory();
        setScans(list);
        if (list.length >= 2) {
          setBaseScanId(list[1].scan_id);
          setTargetScanId(list[0].scan_id);
        } else if (list.length === 1) {
          setBaseScanId(list[0].scan_id);
          setTargetScanId(list[0].scan_id);
        }
      } catch (err) {
        setError("Failed to load past scans for comparison.");
      }
    }
    loadScans();
  }, []);

  const handleCompare = async () => {
    if (!baseScanId || !targetScanId) {
      setError("Please select both a baseline scan and a target scan.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await compareScans(baseScanId, targetScanId);
      setComparison(res);
    } catch (err) {
      setError(err.message || "Failed to compare scans.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Selector Box */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
        <div className="mb-4">
          <h3 className="text-lg font-bold text-white flex items-center space-x-2">
            <GitCompare className="w-5 h-5 text-cyan-400" />
            <span>Fix Verification & Scan Diff</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Compare two scans of the same project to verify that vulnerabilities were properly remediated without introducing new risks.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Baseline Scan (Before Fix)</label>
            <select
              value={baseScanId}
              onChange={(e) => setBaseScanId(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white"
            >
              {scans.map((s) => (
                <option key={s.scan_id} value={s.scan_id}>
                  {s.project_name} ({s.scan_id}) • {new Date(s.created_at).toLocaleTimeString()} ({s.findings_count} findings)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Target Scan (After Fix)</label>
            <select
              value={targetScanId}
              onChange={(e) => setTargetScanId(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white"
            >
              {scans.map((s) => (
                <option key={s.scan_id} value={s.scan_id}>
                  {s.project_name} ({s.scan_id}) • {new Date(s.created_at).toLocaleTimeString()} ({s.findings_count} findings)
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300">
            {error}
          </div>
        )}

        <div className="mt-4 flex justify-end">
          <button
            onClick={handleCompare}
            disabled={loading || !baseScanId || !targetScanId}
            className="px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center space-x-2 transition-all shadow-lg shadow-cyan-600/20 disabled:opacity-50"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <GitCompare className="w-3.5 h-3.5" />}
            <span>Compare & Verify Fixes</span>
          </button>
        </div>
      </div>

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-6">
          {/* Summary counters */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div
              onClick={() => setActiveSubTab("fixed")}
              className={`p-4 rounded-xl cursor-pointer transition-all border ${
                activeSubTab === "fixed"
                  ? "bg-emerald-950/40 border-emerald-500/60"
                  : "bg-slate-900/40 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between text-xs text-emerald-400 font-semibold">
                <span>Fixed Findings</span>
                <CheckCircle2 className="w-4 h-4" />
              </div>
              <div className="text-2xl font-bold text-emerald-300 mt-2">{comparison.summary.fixed}</div>
            </div>

            <div
              onClick={() => setActiveSubTab("new")}
              className={`p-4 rounded-xl cursor-pointer transition-all border ${
                activeSubTab === "new"
                  ? "bg-rose-950/40 border-rose-500/60"
                  : "bg-slate-900/40 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between text-xs text-rose-400 font-semibold">
                <span>New Findings</span>
                <AlertCircle className="w-4 h-4" />
              </div>
              <div className="text-2xl font-bold text-rose-300 mt-2">{comparison.summary.new}</div>
            </div>

            <div
              onClick={() => setActiveSubTab("still_present")}
              className={`p-4 rounded-xl cursor-pointer transition-all border ${
                activeSubTab === "still_present"
                  ? "bg-amber-950/40 border-amber-500/60"
                  : "bg-slate-900/40 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between text-xs text-amber-400 font-semibold">
                <span>Still Present</span>
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div className="text-2xl font-bold text-amber-300 mt-2">{comparison.summary.still_present}</div>
            </div>

            <div
              onClick={() => setActiveSubTab("uncertain")}
              className={`p-4 rounded-xl cursor-pointer transition-all border ${
                activeSubTab === "uncertain"
                  ? "bg-blue-950/40 border-blue-500/60"
                  : "bg-slate-900/40 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between text-xs text-blue-400 font-semibold">
                <span>Uncertain / Shifted</span>
                <RefreshCw className="w-4 h-4" />
              </div>
              <div className="text-2xl font-bold text-blue-300 mt-2">{comparison.summary.uncertain}</div>
            </div>
          </div>

          {/* Detailed list for active sub tab */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-slate-200 uppercase tracking-wider text-xs">
              {activeSubTab === "fixed" && "✓ Verified Remediated Vulnerabilities"}
              {activeSubTab === "new" && "⚠️ Newly Introduced Security Issues"}
              {activeSubTab === "still_present" && "⏳ Unresolved Security Issues"}
              {activeSubTab === "uncertain" && "🔍 Code-Shifted Issues Requiring Review"}
            </h4>

            {activeSubTab === "fixed" && (
              comparison.fixed_findings.length === 0 ? (
                <p className="text-xs text-slate-500 py-6 text-center">No resolved findings detected between these scans.</p>
              ) : (
                comparison.fixed_findings.map((f) => <FindingCard key={f.finding_id} finding={f} />)
              )
            )}

            {activeSubTab === "new" && (
              comparison.new_findings.length === 0 ? (
                <p className="text-xs text-slate-500 py-6 text-center">No new vulnerabilities introduced. Great job!</p>
              ) : (
                comparison.new_findings.map((f) => <FindingCard key={f.finding_id} finding={f} />)
              )
            )}

            {activeSubTab === "still_present" && (
              comparison.still_present_findings.length === 0 ? (
                <p className="text-xs text-slate-500 py-6 text-center">No persistent vulnerabilities remaining.</p>
              ) : (
                comparison.still_present_findings.map((f) => <FindingCard key={f.finding_id} finding={f} />)
              )
            )}

            {activeSubTab === "uncertain" && (
              comparison.uncertain_findings.length === 0 ? (
                <p className="text-xs text-slate-500 py-6 text-center">No uncertain findings.</p>
              ) : (
                comparison.uncertain_findings.map((f) => <FindingCard key={f.finding_id} finding={f} />)
              )
            )}
          </div>
        </div>
      )}
    </div>
  );
}
