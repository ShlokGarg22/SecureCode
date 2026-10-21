"use client";

import React from "react";
import { AlertCircle, AlertTriangle, Info, Clock, FileCode, Download, ShieldAlert, CheckCircle } from "lucide-react";
import { getExportJsonUrl } from "@/lib/api";

export default function MetricsOverview({ scanResult }) {
  if (!scanResult) return null;

  const { severity_breakdown, files_scanned, duration_seconds, scan_id, project_name } = scanResult;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-5">
      {/* Top Banner Details */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
        <div>
          <div className="flex items-center space-x-2.5">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">{project_name}</h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-mono bg-slate-100 text-slate-700 font-semibold border border-slate-200">
              {scan_id}
            </span>
          </div>
          <div className="flex items-center space-x-4 text-xs text-slate-500 mt-1.5">
            <span className="flex items-center space-x-1">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>{duration_seconds}s execution</span>
            </span>
            <span className="flex items-center space-x-1">
              <FileCode className="w-3.5 h-3.5 text-slate-400" />
              <span>{files_scanned} files analyzed</span>
            </span>
            <span className="text-slate-400">•</span>
            <span>Engine: {scanResult.scanners_used?.join(", ") || "Semgrep"}</span>
          </div>
        </div>

        {/* Download JSON Button */}
        <a
          href={getExportJsonUrl(scan_id)}
          download
          className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold border border-slate-200 transition-colors shadow-xs"
        >
          <Download className="w-3.5 h-3.5 text-slate-500" />
          <span>Export JSON Report</span>
        </a>
      </div>

      {/* Severity Counters Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {/* Critical */}
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-rose-700 uppercase tracking-wider">Critical</span>
            <ShieldAlert className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-900 mt-2">
            {severity_breakdown.critical}
          </div>
        </div>

        {/* High */}
        <div className="p-4 rounded-xl bg-orange-50 border border-orange-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-orange-700 uppercase tracking-wider">High</span>
            <AlertCircle className="w-4 h-4 text-orange-600" />
          </div>
          <div className="text-2xl font-bold text-orange-900 mt-2">
            {severity_breakdown.high}
          </div>
        </div>

        {/* Medium */}
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-amber-700 uppercase tracking-wider">Medium</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-900 mt-2">
            {severity_breakdown.medium}
          </div>
        </div>

        {/* Low */}
        <div className="p-4 rounded-xl bg-blue-50 border border-blue-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-blue-700 uppercase tracking-wider">Low</span>
            <Info className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-blue-900 mt-2">
            {severity_breakdown.low}
          </div>
        </div>

        {/* Informational */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">Info</span>
            <Info className="w-4 h-4 text-slate-500" />
          </div>
          <div className="text-2xl font-bold text-slate-800 mt-2">
            {severity_breakdown.informational}
          </div>
        </div>
      </div>
    </div>
  );
}
