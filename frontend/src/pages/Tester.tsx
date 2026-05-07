import { useEffect, useRef, useState } from "react";
import { BuildLog } from "../components/BuildLog";
import { DeviceFrame, type DeviceKind } from "../components/DeviceFrame";
import { SettingsDialog } from "../components/SettingsDialog";
import { StatusPill } from "../components/StatusPill";
import { SubmitForm, type SubmitInput } from "../components/SubmitForm";
import {
  createBuildFromGithub,
  createBuildFromZip,
  getBuild,
  getToken,
  previewUrl,
} from "../lib/api";
import type { BuildDetail } from "../lib/types";

const TERMINAL: BuildDetail["state"][] = ["ready", "failed", "cancelled"];

export function Tester(): JSX.Element {
  const [build, setBuild] = useState<BuildDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [device, setDevice] = useState<DeviceKind>("phone");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    // Backend URL is optional: if blank, the SPA falls back to same-origin
    // (works when the bundle is served from the FastAPI process). The shared
    // tester token, on the other hand, is always required.
    if (!getToken()) {
      setSettingsOpen(true);
    }
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, []);

  useEffect(() => {
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
    if (!build || TERMINAL.includes(build.state)) return;
    pollRef.current = window.setInterval(async () => {
      try {
        const next = await getBuild(build.id);
        setBuild(next);
        if (TERMINAL.includes(next.state) && pollRef.current) {
          window.clearInterval(pollRef.current);
          pollRef.current = null;
        }
      } catch {
        // ignore polling errors; UI shows stale logs.
      }
    }, 1000);
    // build object identity is irrelevant; we only want to re-arm on id/state changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [build?.id, build?.state]);

  const onSubmit = async (input: SubmitInput) => {
    setBusy(true);
    try {
      const summary =
        input.kind === "github"
          ? await createBuildFromGithub({
              github_url: input.github_url,
              branch: input.branch,
              project_subdir: input.project_subdir,
            })
          : await createBuildFromZip({
              file: input.file,
              project_subdir: input.project_subdir,
            });
      const detail = await getBuild(summary.id);
      setBuild(detail);
    } finally {
      setBusy(false);
    }
  };

  const preview = build && build.state === "ready" ? previewUrl(build.id) : null;

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      <header className="flex items-center justify-between border-b border-neutral-800 bg-neutral-900 px-6 py-3">
        <div>
          <h1 className="text-base font-semibold">Flutter Tester</h1>
          <p className="text-xs text-neutral-400">
            Build any Flutter app from a GitHub URL or zip and run it in your browser.
          </p>
        </div>
        <button
          onClick={() => setSettingsOpen(true)}
          className="rounded border border-neutral-700 px-3 py-1.5 text-sm hover:bg-neutral-800"
        >
          Settings
        </button>
      </header>

      <main className="grid grid-cols-1 gap-6 p-6 lg:grid-cols-[360px_1fr]">
        <section className="space-y-4">
          <SubmitForm onSubmit={onSubmit} busy={busy} />

          {build && (
            <div className="rounded border border-neutral-800 bg-neutral-900 p-4">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-medium">Build {build.id}</span>
                <StatusPill state={build.state} />
              </div>
              <p className="mb-3 break-all text-xs text-neutral-400">{build.source_label}</p>
              {build.error && (
                <p className="mb-3 rounded bg-rose-950/40 px-3 py-2 text-xs text-rose-300">
                  {build.error}
                </p>
              )}
              <BuildLog text={build.logs} />
            </div>
          )}
        </section>

        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-neutral-300">Preview</h2>
            <div className="flex gap-2 text-xs">
              {(["phone", "tablet", "desktop"] as DeviceKind[]).map((d) => (
                <button
                  key={d}
                  onClick={() => setDevice(d)}
                  className={`rounded-full px-3 py-1 ${device === d ? "bg-sky-600 text-white" : "bg-neutral-800 text-neutral-300"}`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>
          <div className="rounded border border-neutral-800 bg-neutral-900 p-4">
            {preview ? (
              <DeviceFrame device={device}>
                <iframe
                  key={preview}
                  src={preview}
                  title="Flutter app preview"
                  className="h-full w-full border-0"
                  allow="autoplay; clipboard-read; clipboard-write; fullscreen"
                />
              </DeviceFrame>
            ) : (
              <p className="py-24 text-center text-sm text-neutral-500">
                {build ? "Waiting for build to finish…" : "Submit a project on the left to begin."}
              </p>
            )}
          </div>
        </section>
      </main>

      <SettingsDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
