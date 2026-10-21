/**
 * Enhanced API client with authentication, error handling, and loading states.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

// Token storage utilities
const TOKEN_KEY = 'diffguard_auth_token';

export function storeToken(token) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function getToken() {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
}

export function clearToken() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function isAuthenticated() {
  return !!getToken();
}

// Enhanced fetch with authentication and error handling
async function fetchWithAuth(url, options = {}) {
  const token = getToken();
  const headers = {
    ...options.headers,
    'Content-Type': 'application/json',
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const defaultOptions = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${url}`, defaultOptions);
    
    // Handle authentication errors
    if (response.status === 401) {
      clearToken();
      throw new Error('Authentication required. Please login again.');
    }
    
    if (response.status === 403) {
      throw new Error('Insufficient permissions for this action.');
    }
    
    if (response.status === 429) {
      const retryAfter = response.headers.get('Retry-After') || '60';
      throw new Error(`Rate limit exceeded. Please try again in ${retryAfter} seconds.`);
    }
    
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        // If response is not JSON, use status text
        errorMessage = response.statusText || errorMessage;
      }
      throw new Error(errorMessage);
    }
    
    // Parse JSON if content-type is JSON
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    
    return response;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

// Auth API
export async function getDemoTokens() {
  const response = await fetchWithAuth('/api/auth/demo-tokens');
  return response;
}

export async function verifyAuth() {
  try {
    const response = await fetchWithAuth('/api/auth/verify');
    return response;
  } catch (error) {
    return { authenticated: false, error: error.message };
  }
}

// Health check (no auth required)
export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`, { method: "GET" });
    if (!res.ok) throw new Error("Health check failed");
    return await res.json();
  } catch (error) {
    return {
      status: "unreachable",
      scanners: { semgrep_installed: false, gitleaks_installed: false },
      error: error.message
    };
  }
}

export async function uploadAndScanProject(file, projectName, ruleMode = "bundled", enableAi = true) {
  const formData = new FormData();
  formData.append("file", file);
  if (projectName) formData.append("project_name", projectName);
  formData.append("rule_mode", ruleMode);
  formData.append("enable_ai", enableAi ? "true" : "false");

  const res = await fetch(`${API_BASE_URL}/api/scans/upload`, {
    method: "POST",
    body: formData,
    headers: {
      'Authorization': `Bearer ${getToken()}`,
    },
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: "Scan request failed" }));
    throw new Error(errData.detail || `Scan failed with status ${res.status}`);
  }

  return await res.json();
}

export async function getScanHistory() {
  return await fetchWithAuth('/api/scans', { method: "GET" });
}

export async function getScanDetails(scanId) {
  return await fetchWithAuth(`/api/scans/${scanId}`, { method: "GET" });
}

export async function compareScans(baseScanId, targetScanId) {
  return await fetchWithAuth(`/api/scans/${baseScanId}/compare/${targetScanId}`, { method: "GET" });
}

export function getExportJsonUrl(scanId) {
  return `${API_BASE_URL}/api/scans/${scanId}/export/json`;
}

export function getExportPatchUrl(scanId) {
  return `${API_BASE_URL}/api/scans/${scanId}/export/patch`;
}

export function getExportSarifUrl(scanId) {
  return `${API_BASE_URL}/api/scans/${scanId}/export/sarif`;
}

export async function downloadExportFile(url, fallbackFilename) {
  const token = getToken();
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = await fetch(url, { headers });
  if (!res.ok) {
    throw new Error(`Export download failed: ${res.statusText}`);
  }
  const blob = await res.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = fallbackFilename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

export async function exportScanAsPatch(scanId) {
  return downloadExportFile(getExportPatchUrl(scanId), `remediation-${scanId}.patch`);
}

export async function exportScanAsSARIF(scanId) {
  return downloadExportFile(getExportSarifUrl(scanId), `diffguard-${scanId}.sarif`);
}

export async function exportScanAsJSON(scanId) {
  return downloadExportFile(getExportJsonUrl(scanId), `diffguard-${scanId}.json`);
}