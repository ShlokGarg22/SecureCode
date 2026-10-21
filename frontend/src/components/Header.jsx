"use client";

import React, { useEffect, useState } from "react";
import { ShieldCheck, FileText, History, Sparkles, CheckCircle2, LogOut, User, Lock } from "lucide-react";
import { checkBackendHealth, isAuthenticated, clearToken } from "@/lib/api_enhanced";

export default function Header({ activeTab, setActiveTab, hasReport, isAuthenticated: userAuthenticated }) {
  const [health, setHealth] = useState({ status: "checking", scanners: {} });
  const [authStatus, setAuthStatus] = useState(false);

  useEffect(() => {
    async function fetchHealth() {
      const data = await checkBackendHealth();
      setHealth(data);
    }
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    setAuthStatus(userAuthenticated);
  }, [userAuthenticated]);

  const isOnline = health.status === "healthy";

  const handleLogout = () => {
    clearToken();
    window.location.reload();
  };

  return (
    <header className="border-b border-slate-200 bg-white/95 backdrop-blur-md sticky top-0 z-50 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab("scan")}>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-md shadow-blue-500/20">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold tracking-tight text-slate-900">DiffGuard</span>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
                AI Security Reviewer
              </span>
            </div>
            <p className="text-[11px] text-slate-500">Autonomous Code Vulnerability & Remediation Engine</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl border border-slate-200">
          <button
            onClick={() => setActiveTab("scan")}
            className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
              activeTab === "scan"
                ? "bg-white text-slate-900 shadow-xs border border-slate-200"
                : "text-slate-600 hover:text-slate-900"
            }`}
            aria-label="Code scanner tab"
          >
            <ShieldCheck className="w-4 h-4 text-blue-600" aria-hidden="true" />
            <span>Code Scanner</span>
          </button>

          <button
            onClick={() => setActiveTab("report")}
            className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
              activeTab === "report"
                ? "bg-white text-slate-900 shadow-xs border border-slate-200"
                : "text-slate-600 hover:text-slate-900"
            }`}
            aria-label="Security report and diffs tab"
          >
            <FileText className="w-4 h-4 text-indigo-600" aria-hidden="true" />
            <span>Security Report & Diffs</span>
            {hasReport && (
              <span className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse" aria-label="Active report available" />
            )}
          </button>

          <button
            onClick={() => setActiveTab("history")}
            className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
              activeTab === "history"
                ? "bg-white text-slate-900 shadow-xs border border-slate-200"
                : "text-slate-600 hover:text-slate-900"
            }`}
            aria-label="Scan history tab"
          >
            <History className="w-4 h-4 text-slate-600" aria-hidden="true" />
            <span>Scan History</span>
          </button>
        </nav>

        {/* Status indicators */}
        <div className="hidden sm:flex items-center space-x-2 text-xs">
          {/* Authentication status */}
          <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full border ${
            authStatus 
              ? "bg-green-50 border-green-200 text-green-700" 
              : "bg-amber-50 border-amber-200 text-amber-700"
          }`}>
            {authStatus ? (
              <>
                <CheckCircle2 className="w-3 h-3 text-green-600" aria-hidden="true" />
                <span className="font-medium text-[11px]">Authenticated</span>
                <button
                  onClick={handleLogout}
                  className="ml-1 text-amber-600 hover:text-amber-800"
                  aria-label="Log out"
                >
                  <LogOut className="w-3 h-3" />
                </button>
              </>
            ) : (
              <>
                <Lock className="w-3 h-3 text-amber-600" aria-hidden="true" />
                <span className="font-medium text-[11px]">Unauthenticated</span>
              </>
            )}
          </div>

          {/* Connection status */}
          <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full border ${
            isOnline 
              ? "bg-blue-50 border-blue-200 text-blue-700" 
              : "bg-rose-50 border-rose-200 text-rose-700"
          }`}>
            <span className={`w-2 h-2 rounded-full ${isOnline ? "bg-emerald-500" : "bg-rose-500"}`} aria-hidden="true" />
            <span className="font-medium text-[11px]">{isOnline ? "Backend Live" : "Backend Offline"}</span>
          </div>

          {/* AI Status */}
          <span className="text-[11px] font-mono text-slate-400 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            AI: {health.ai_provider_configured || "Ready"}
          </span>
        </div>
      </div>
    </header>
  );
}