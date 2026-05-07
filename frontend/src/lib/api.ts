import type { BuildDetail, BuildSummary } from "./types";

const TOKEN_KEY = "flutter-tester:token";
const BACKEND_KEY = "flutter-tester:backend-url";

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) ?? "";
}

export function setToken(value: string): void {
  localStorage.setItem(TOKEN_KEY, value.trim());
}

export function getBackendUrl(): string {
  // Order: explicit override in localStorage > VITE_BACKEND_URL build-time env > same origin.
  const override = localStorage.getItem(BACKEND_KEY);
  if (override) return override.replace(/\/$/, "");
  const fromEnv = (import.meta as unknown as { env?: { VITE_BACKEND_URL?: string } }).env
    ?.VITE_BACKEND_URL;
  if (fromEnv) return fromEnv.replace(/\/$/, "");
  return "";
}

export function setBackendUrl(value: string): void {
  localStorage.setItem(BACKEND_KEY, value.trim().replace(/\/$/, ""));
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { "X-Tester-Token": token } : {};
}

async function jsonOrThrow<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`${resp.status} ${resp.statusText}: ${text || "request failed"}`);
  }
  return (await resp.json()) as T;
}

export async function createBuildFromGithub(input: {
  github_url: string;
  branch?: string;
  project_subdir?: string;
}): Promise<BuildSummary> {
  const resp = await fetch(`${getBackendUrl()}/api/builds`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(input),
  });
  return jsonOrThrow<BuildSummary>(resp);
}

export async function createBuildFromZip(input: {
  file: File;
  project_subdir?: string;
}): Promise<BuildSummary> {
  const fd = new FormData();
  fd.append("file", input.file);
  if (input.project_subdir) fd.append("project_subdir", input.project_subdir);
  const resp = await fetch(`${getBackendUrl()}/api/builds/upload`, {
    method: "POST",
    headers: authHeaders(),
    body: fd,
  });
  return jsonOrThrow<BuildSummary>(resp);
}

export async function getBuild(id: string): Promise<BuildDetail> {
  const resp = await fetch(`${getBackendUrl()}/api/builds/${id}`, {
    headers: authHeaders(),
  });
  return jsonOrThrow<BuildDetail>(resp);
}

export async function listBuilds(): Promise<BuildSummary[]> {
  const resp = await fetch(`${getBackendUrl()}/api/builds`, {
    headers: authHeaders(),
  });
  return jsonOrThrow<BuildSummary[]>(resp);
}

export function previewUrl(buildId: string): string {
  return `${getBackendUrl()}/preview/${buildId}/`;
}
