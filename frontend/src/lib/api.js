const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

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
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: "Scan request failed" }));
    throw new Error(errData.detail || `Scan failed with status ${res.status}`);
  }

  return await res.json();
}

export async function getScanHistory() {
  const res = await fetch(`${API_BASE_URL}/api/scans`, { method: "GET" });
  if (!res.ok) throw new Error("Failed to fetch scan history");
  return await res.json();
}

export async function getScanDetails(scanId) {
  const res = await fetch(`${API_BASE_URL}/api/scans/${scanId}`, { method: "GET" });
  if (!res.ok) throw new Error("Failed to fetch scan details");
  return await res.json();
}

export async function compareScans(baseScanId, targetScanId) {
  const res = await fetch(`${API_BASE_URL}/api/scans/${baseScanId}/compare/${targetScanId}`, { method: "GET" });
  if (!res.ok) throw new Error("Failed to compare scans");
  return await res.json();
}

export function getExportJsonUrl(scanId) {
  return `${API_BASE_URL}/api/scans/${scanId}/export/json`;
}
