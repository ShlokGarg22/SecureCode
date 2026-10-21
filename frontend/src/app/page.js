"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/Header";
import UploadZone from "@/components/UploadZone";
import MetricsOverview from "@/components/MetricsOverview";
import FindingCard from "@/components/FindingCard";
import ScanHistory from "@/components/ScanHistory";
import { Search, Filter, ShieldCheck, Sparkles, FileText, ArrowRight, Download, RefreshCw, AlertCircle, Loader } from "lucide-react";
import { getExportJsonUrl, exportScanAsPatch, exportScanAsSARIF, exportScanAsJSON } from "@/lib/api_enhanced";

export default function Home() {
  const [activeTab, setActiveTab] = useState("scan");
  const [currentScan, setCurrentScan] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState("all");
  const [selectedTool, setSelectedTool] = useState("all");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check authentication on component mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // In a real app, verify token validity with backend
      const token = localStorage.getItem('diffguard_auth_token');
      setIsAuthenticated(!!token);
    } catch (err) {
      console.error('Auth check failed:', err);
      setIsAuthenticated(false);
    }
  };

  const handleScanComplete = (scanResult) => {
    setCurrentScan(scanResult);
    setActiveTab("report"); // Automatically transition to the Code Diff Report page
    setError(null); // Clear any previous errors
  };

  const handleScanError = (errorMsg) => {
    setError(errorMsg);
    setIsLoading(false);
  };

  const clearError = () => {
    setError(null);
  };

  const findings = currentScan?.findings || [];
  const filteredFindings = findings.filter((f) => {
    const matchesQuery =
      searchQuery === "" ||
      f.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.file_path?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.rule_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.description?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesSeverity =
      selectedSeverity === "all" || f.severity?.toLowerCase() === selectedSeverity.toLowerCase();

    const matchesTool =
      selectedTool === "all" || f.tool?.toLowerCase() === selectedTool.toLowerCase();

    return matchesQuery && matchesSeverity && matchesTool;
  });

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Light Theme Navigation Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        hasReport={!!currentScan}
        isAuthenticated={isAuthenticated}
      />

      {/* Error Alert */}
      {error && (
        <div className="mx-4 mt-4 p-4 rounded-xl bg-red-50 border border-red-200 flex items-start justify-between" role="alert" aria-live="polite">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" aria-hidden="true" />
            <div>
              <h4 className="text-sm font-bold text-red-900">Scan Error</h4>
              <p className="text-xs text-red-700 mt-0.5">{error}</p>
            </div>
          </div>
          <button
            onClick={clearError}
            className="text-xs text-red-600 hover:text-red-800 font-medium"
            aria-label="Dismiss error message"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* TAB 1: CODE SCANNER (UPLOAD) */}
        {activeTab === "scan" && (
          <div className="space-y-6">
            <UploadZone 
              onScanComplete={handleScanComplete} 
              onScanError={handleScanError}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
              isAuthenticated={isAuthenticated}
            />

            {/* Quick status banner if a scan is already active */}
            {currentScan && (
              <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-between" role="status">
                <div>
                  <h4 className="text-sm font-bold text-blue-900">Active Report Available</h4>
                  <p className="text-xs text-blue-700 mt-0.5">
                    {currentScan.project_name} ({currentScan.findings_count} security findings identified with AI code diffs).
                  </p>
                </div>
                <button
                  onClick={() => setActiveTab("report")}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-xs focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  aria-label="View security report with code diffs"
                >
                  <span>View Code Diffs</span>
                  <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: SECURITY REPORT & CODE DIFFS PAGE */}
        {activeTab === "report" && (
          <div className="space-y-6">
            {currentScan ? (
              <>
                {/* Metrics Banner */}
                <MetricsOverview scanResult={currentScan} />

                {/* Search & Filter Bar */}
                <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
                  {/* Search box */}
                  <div className="relative flex-1">
                    <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" aria-hidden="true" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search findings by file, rule, or vulnerability..."
                      className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                      aria-label="Search security findings"
                    />
                  </div>

                  {/* Filters */}
                  <div className="flex items-center space-x-2">
                    <select
                      value={selectedSeverity}
                      onChange={(e) => setSelectedSeverity(e.target.value)}
                      className="px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-medium"
                      aria-label="Filter by severity level"
                    >
                      <option value="all">All Severities</option>
                      <option value="critical">Critical</option>
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                      <option value="informational">Info</option>
                    </select>

                    <select
                      value={selectedTool}
                      onChange={(e) => setSelectedTool(e.target.value)}
                      className="px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-medium"
                      aria-label="Filter by security tool"
                    >
                      <option value="all">All Scanners</option>
                      <option value="semgrep">Semgrep</option>
                      <option value="gitleaks">Gitleaks</option>
                    </select>
                  </div>
                </div>

                {/* Findings List with Side-by-Side Diffs */}
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <h2 className="text-xs font-bold text-slate-600 uppercase tracking-wider">
                      Vulnerability Findings & AI Remediation Diffs ({filteredFindings.length} of {findings.length})
                    </h2>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => exportScanAsPatch(currentScan.scan_id)}
                        className="inline-flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 text-xs font-semibold transition-colors shadow-xs"
                        title="Download standard unified Git patch to apply all fixes via 'git apply remediation.patch'"
                      >
                        <Download className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Git Patch (.patch)</span>
                      </button>
                      <button
                        onClick={() => exportScanAsSARIF(currentScan.scan_id)}
                        className="inline-flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 text-xs font-semibold transition-colors shadow-xs"
                        title="Download SARIF v2.1.0 report for GitHub Security tab or IDEs"
                      >
                        <Download className="w-3.5 h-3.5 text-blue-600" />
                        <span>SARIF (GitHub)</span>
                      </button>
                      <button
                        onClick={() => exportScanAsJSON(currentScan.scan_id)}
                        className="inline-flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-semibold transition-colors shadow-xs"
                        title="Download raw JSON report"
                      >
                        <Download className="w-3.5 h-3.5 text-slate-500" />
                        <span>JSON</span>
                      </button>
                    </div>
                  </div>

                  {filteredFindings.length === 0 ? (
                    <div className="p-12 text-center bg-white border border-slate-200 rounded-xl text-xs text-slate-500 shadow-xs" role="status">
                      No findings match the current search filters.
                    </div>
                  ) : (
                    filteredFindings.map((finding) => (
                      <FindingCard key={finding.finding_id} finding={finding} />
                    ))
                  )}
                </div>
              </>
            ) : (
              <div className="p-16 text-center bg-white border border-slate-200 rounded-2xl shadow-xs space-y-4" role="status">
                <div className="w-12 h-12 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center mx-auto text-blue-600">
                  <FileText className="w-6 h-6" aria-hidden="true" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">No Security Report Loaded Yet</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Upload a project in the Scanner tab or select a previous report from Scan History to inspect side-by-side code diffs.
                  </p>
                </div>
                <button
                  onClick={() => setActiveTab("scan")}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-colors shadow-xs focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  aria-label="Go to scanner to upload project"
                >
                  Go to Scanner
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: SCAN HISTORY */}
        {activeTab === "history" && (
          <ScanHistory
            onSelectScan={(scan) => {
              setCurrentScan(scan);
              setActiveTab("report"); // Opens report page immediately
              setError(null);
            }}
            isAuthenticated={isAuthenticated}
          />
        )}
      </main>

      {/* Loading Overlay */}
      {isLoading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" role="status" aria-live="polite">
          <div className="bg-white p-6 rounded-xl shadow-lg flex flex-col items-center space-y-3">
            <Loader className="w-8 h-8 text-blue-600 animate-spin" aria-hidden="true" />
            <p className="text-sm font-medium text-slate-700">Scanning project...</p>
            <p className="text-xs text-slate-500">This may take a moment</p>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-200 py-6 bg-white text-center text-xs text-slate-500">
        <p>DiffGuard • AI-Powered Security Code Reviewer with Side-by-Side Code Diffs</p>
      </footer>
    </div>
  );
}
