import { useEffect, useState } from "react";
import { getBackendUrl, getToken, setBackendUrl, setToken } from "../lib/api";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function SettingsDialog({ open, onClose }: Props): JSX.Element | null {
  const [token, setLocalToken] = useState("");
  const [backend, setLocalBackend] = useState("");

  useEffect(() => {
    if (open) {
      setLocalToken(getToken());
      setLocalBackend(getBackendUrl());
    }
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-lg border border-neutral-800 bg-neutral-900 p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Settings</h2>
        <label className="mb-3 block text-sm">
          <span className="mb-1 block text-neutral-400">Backend URL</span>
          <input
            value={backend}
            onChange={(e) => setLocalBackend(e.target.value)}
            placeholder="https://flutter-tester.fly.dev"
            className="w-full rounded border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
          />
        </label>
        <label className="mb-4 block text-sm">
          <span className="mb-1 block text-neutral-400">Tester Token</span>
          <input
            value={token}
            onChange={(e) => setLocalToken(e.target.value)}
            type="password"
            placeholder="paste your shared secret"
            className="w-full rounded border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
          />
        </label>
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded border border-neutral-700 px-3 py-1.5 text-sm hover:bg-neutral-800"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              setBackendUrl(backend);
              setToken(token);
              onClose();
            }}
            className="rounded bg-sky-600 px-3 py-1.5 text-sm font-medium hover:bg-sky-500"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
