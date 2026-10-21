"use client";

import React, { useState, useEffect } from "react";
import { History, FileCode, Clock, ShieldAlert, ArrowRight, Download, RefreshCw } from "lucide-react";
import { getScanHistory, getScanDetails, getExportJsonUrl } from "@/lib/api";

export default function ScanHistory({ onSelectScan }) {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchScans = async () => {
    setLoading(true);
    try {
      const data = await getScanHistory();
      setScans(data);
      setError(null);
    } catch (err) {
      setError("Failed to load historical scan logs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScans();
  }, []);

  const handleInspect = async (scanId) => {
    try {
      const fullScan = await getScanDetails(scanId);
      onSelectScan(fullScan);
    } catch (err) {
      alert("Failed to load scan details.");
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-100">
        <div>
          <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <History className="w-5 h-5 text-blue-600" />
            <span>Scan History</span>
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Access previous security audit reports, inspect code diffs, and download compliance logs.
          </p>
        </div>

        <button
          onClick={fetchScans}
          className="p-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors"
          title="Refresh History"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {error && (
        <div className="p-3 mb-4 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700">
          {error}
        </div>
      )}

      {loading && scans.length === 0 ? (
        <div className="py-12 text-center text-xs text-slate-500">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-600" />
          <span>Loading historical scans...</span>
        </div>
      ) : scans.length === 0 ? (
        <div className="py-12 text-center text-xs text-slate-500">
          No previous scans found. Run your first project scan to get started!
        </div>
      ) : (
        <div className="divide-y divide-slate-100">
          {scans.map((scan) => (
            <div
              key={scan.scan_id}
              className="py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-50 px-3 rounded-xl transition-colors"
            >
              <div>
                <div className="flex items-center space-x-2.5">
                  <h4 className="text-sm font-bold text-slate-900">{scan.project_name}</h4>
                  <span className="text-xs px-2 py-0.5 rounded-md font-mono bg-slate-100 text-slate-600 border border-slate-200">
                    {scan.scan_id}
                  </span>
                </div>
                <div className="flex items-center space-x-3 text-xs text-slate-500 mt-1">
                  <span>{new Date(scan.created_at).toLocaleString()}</span>
                  <span>•</span>
                  <span>{scan.duration_seconds}s execution</span>
                  <span>•</span>
                  <span>{scan.files_scanned} files analyzed</span>
                </div>
              </div>

              {/* Severity breakdown pill & buttons */}
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-1.5 text-xs font-mono">
                  <span className="px-2 py-0.5 rounded-md bg-rose-50 text-rose-700 border border-rose-200 font-semibold">
                    C: {scan.severity_breakdown.critical}
                  </span>
                  <span className="px-2 py-0.5 rounded-md bg-orange-50 text-orange-700 border border-orange-200 font-semibold">
                    H: {scan.severity_breakdown.high}
                  </span>
                  <span className="px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 border border-amber-200 font-semibold">
                    M: {scan.severity_breakdown.medium}
                  </span>
                </div>

                <button
                  onClick={() => handleInspect(scan.scan_id)}
                  className="px-3.5 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold border border-blue-200 transition-colors flex items-center space-x-1"
                >
                  <span>View Diffs</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>

                <a
                  href={getExportJsonUrl(scan.scan_id)}
                  download
                  className="p-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 text-xs transition-colors"
                  title="Download JSON Report"
                >
                  <Download className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
