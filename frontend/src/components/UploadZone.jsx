"use client";

import React, { useState, useRef, useEffect } from "react";
import { UploadCloud, FileArchive, Sparkles, AlertTriangle, Play, Loader2, ShieldCheck, Zap, Key, AlertCircle, Lock } from "lucide-react";
import { uploadAndScanProject, getDemoTokens, storeToken, isAuthenticated } from "@/lib/api_enhanced";

export default function UploadZone({ onScanComplete, onScanError, isLoading, setIsLoading, isAuthenticated }) {
  const [file, setFile] = useState(null);
  const [projectName, setProjectName] = useState("");
  const [error, setError] = useState(null);
  const [authError, setAuthError] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    // Check auth on mount
    if (!isAuthenticated) {
      setAuthError("Authentication required. Please get a demo token first.");
    } else {
      setAuthError(null);
    }
  }, [isAuthenticated]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (!selected.name.toLowerCase().endsWith(".zip")) {
        setError("Only .zip files are supported.");
        return;
      }
      
      // Check file size (client-side validation)
      const maxSize = 100 * 1024 * 1024; // 100MB
      if (selected.size > maxSize) {
        setError(`File size (${(selected.size / 1024 / 1024).toFixed(2)} MB) exceeds maximum allowed (100 MB)`);
        return;
      }
      
      setFile(selected);
      setError(null);
      if (!projectName) {
        setProjectName(selected.name.replace(".zip", ""));
      }
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const dropped = e.dataTransfer.files[0];
      if (!dropped.name.toLowerCase().endsWith(".zip")) {
        setError("Only .zip archives are supported.");
        return;
      }
      
      // Check file size
      const maxSize = 100 * 1024 * 1024; // 100MB
      if (dropped.size > maxSize) {
        setError(`File size (${(dropped.size / 1024 / 1024).toFixed(2)} MB) exceeds maximum allowed (100 MB)`);
        return;
      }
      
      setFile(dropped);
      setError(null);
      if (!projectName) {
        setProjectName(dropped.name.replace(".zip", ""));
      }
    }
  };

  const handleGetDemoToken = async (role = "analyst") => {
    try {
      setIsLoading(true);
      const response = await getDemoTokens();
      const token = response.tokens[role];
      if (token) {
        storeToken(token);
        setAuthError(null);
        setShowAuthModal(false);
        // Refresh page or trigger parent to update auth state
        window.location.reload();
      }
    } catch (err) {
      setAuthError(`Failed to get demo token: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const startScan = async () => {
    // Check authentication first
    if (!isAuthenticated) {
      setShowAuthModal(true);
      return;
    }

    if (!file) {
      setError("Please select or drop a source code ZIP file.");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      // AI review is always enabled for rich context and side-by-side diffs
      const result = await uploadAndScanProject(file, projectName, "bundled", true);
      onScanComplete(result);
    } catch (err) {
      const errorMsg = err.message || "Scan failed. Please check the backend connection.";
      setError(errorMsg);
      onScanError?.(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs">
      {/* Authentication Modal */}
      {showAuthModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" role="dialog" aria-modal="true">
          <div className="bg-white p-6 rounded-xl shadow-lg w-full max-w-md mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                <Lock className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900">Authentication Required</h3>
                <p className="text-sm text-slate-600">You need a token to scan projects.</p>
              </div>
            </div>

            <div className="space-y-3 mb-6">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  For demo purposes, you can get a temporary token with different access levels:
                </p>
              </div>

              <button
                onClick={() => handleGetDemoToken("viewer")}
                disabled={isLoading}
                className="w-full p-3 text-left border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                <div className="font-medium text-slate-900">Viewer Token</div>
                <div className="text-xs text-slate-500 mt-1">Can view reports only (read-only)</div>
              </button>

              <button
                onClick={() => handleGetDemoToken("analyst")}
                disabled={isLoading}
                className="w-full p-3 text-left border border-blue-200 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors disabled:opacity-50"
              >
                <div className="font-medium text-blue-900">Analyst Token (Recommended)</div>
                <div className="text-xs text-blue-700 mt-1">Can initiate scans and view reports</div>
              </button>

              <button
                onClick={() => handleGetDemoToken("admin")}
                disabled={isLoading}
                className="w-full p-3 text-left border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                <div className="font-medium text-slate-900">Admin Token</div>
                <div className="text-xs text-slate-500 mt-1">Full access including user management</div>
              </button>
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setShowAuthModal(false)}
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={() => handleGetDemoToken("analyst")}
                disabled={isLoading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg disabled:opacity-50"
              >
                {isLoading ? "Getting token..." : "Get Analyst Token"}
              </button>
            </div>

            {authError && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700">{authError}</p>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-6">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>AI Code Security Reviewer</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Project Vulnerability Analysis</h2>
          <p className="text-sm text-slate-500 mt-1">
            Upload your source project to identify vulnerabilities, inspect exploit vectors, and receive side-by-side code fixes.
          </p>

          {/* Authentication Status */}
          {!isAuthenticated && (
            <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center justify-center space-x-2">
              <Key className="w-4 h-4 text-amber-600" />
              <span className="text-sm text-amber-800">Authentication required to scan projects</span>
              <button
                onClick={() => setShowAuthModal(true)}
                className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white text-xs font-medium rounded"
              >
                Get Token
              </button>
            </div>
          )}

          {isAuthenticated && (
            <div className="mt-4 p-2 bg-green-50 border border-green-200 rounded-lg inline-flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-800">Authenticated ✓</span>
            </div>
          )}
        </div>

        {/* Dropzone */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => isAuthenticated && fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${isAuthenticated ? 'cursor-pointer' : 'cursor-not-allowed opacity-70'} ${
            file
              ? "border-blue-500 bg-blue-50/50"
              : "border-slate-300 hover:border-slate-400 bg-slate-50/60 hover:bg-slate-50"
          }`}
          aria-label={isAuthenticated ? "Drag and drop or click to select ZIP file" : "Authentication required to upload files"}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".zip"
            className="hidden"
            aria-label="Select project ZIP file"
            disabled={!isAuthenticated}
          />

          <div className="flex flex-col items-center justify-center space-y-3">
            <div className={`w-14 h-14 rounded-full flex items-center justify-center shadow-xs transition-colors ${
              file ? "bg-blue-600 text-white" : "bg-white text-slate-500 border border-slate-200"
            }`}>
              {file ? <FileArchive className="w-7 h-7" /> : <UploadCloud className="w-7 h-7" />}
            </div>

            {file ? (
              <div>
                <p className="text-sm font-bold text-slate-900">{file.name}</p>
                <p className="text-xs text-slate-500 mt-0.5">{(file.size / 1024 / 1024).toFixed(2)} MB • Ready for AI Security Review</p>
              </div>
            ) : (
              <div>
                <p className="text-sm font-semibold text-slate-800">
                  {isAuthenticated ? (
                    <span className="text-blue-600 hover:underline">Click to browse</span>
                  ) : (
                    <span className="text-slate-400">Authentication required</span>
                  )}
                  <span> or drag and drop your project ZIP</span>
                </p>
                <p className="text-xs text-slate-500 mt-1">Accepts .ZIP archives up to 100MB (Python, JavaScript/TypeScript, Go, Java, PHP)</p>
              </div>
            )}
          </div>
        </div>

        {/* Project Name Field */}
        <div className="mt-5">
          <label className="block text-xs font-semibold text-slate-700 mb-1" htmlFor="project-name">
            Project Name (Optional)
          </label>
          <input
            id="project-name"
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="e.g. BankingApp-v1"
            className="w-full px-3.5 py-2 text-sm bg-white border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
            disabled={!isAuthenticated}
          />
        </div>

        {/* Feature Highlights Pills */}
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
          <div className="flex items-center space-x-2 p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-700">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>Static Engine Detection</span>
          </div>
          <div className="flex items-center space-x-2 p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-700">
            <Sparkles className="w-4 h-4 text-purple-600 shrink-0" />
            <span>AI Attack Scenario Exploit</span>
          </div>
          <div className="flex items-center space-x-2 p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-700">
            <Zap className="w-4 h-4 text-blue-600 shrink-0" />
            <span>Side-by-Side Code Diffs</span>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 flex items-center space-x-2 text-rose-700 text-xs" role="alert">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-500" />
            <span>{error}</span>
          </div>
        )}

        {/* Action Button */}
        <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-slate-100">
          <span className="text-xs text-slate-500">
            Tip: You can use <span className="font-mono font-semibold text-slate-700">demo_vulnerable_project.zip</span> from your workspace
          </span>

          <button
            onClick={startScan}
            disabled={!file || !isAuthenticated || isLoading}
            className={`w-full sm:w-auto px-6 py-2.5 rounded-xl font-semibold text-sm flex items-center justify-center space-x-2 shadow-sm transition-all ${
              !file || !isAuthenticated || isLoading
                ? "bg-slate-200 text-slate-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 text-white shadow-blue-600/20 active:scale-[0.99] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            }`}
            aria-label={!isAuthenticated ? "Authentication required to start scan" : "Start security scan"}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                <span>Analyzing & Generating AI Diffs...</span>
              </>
            ) : !isAuthenticated ? (
              <>
                <Lock className="w-4 h-4" aria-hidden="true" />
                <span>Authentication Required</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" aria-hidden="true" />
                <span>Run AI Security Review</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}