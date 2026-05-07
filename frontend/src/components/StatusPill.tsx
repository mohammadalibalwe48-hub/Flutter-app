import type { BuildState } from "../lib/types";

const STYLES: Record<BuildState, string> = {
  queued: "bg-neutral-700 text-neutral-200",
  preparing: "bg-amber-700 text-amber-100",
  installing: "bg-amber-700 text-amber-100",
  building: "bg-sky-700 text-sky-100",
  ready: "bg-emerald-700 text-emerald-100",
  failed: "bg-rose-700 text-rose-100",
  cancelled: "bg-neutral-700 text-neutral-300",
};

export function StatusPill({ state }: { state: BuildState }): JSX.Element {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-0.5 text-xs font-medium ${STYLES[state]}`}
    >
      {state}
    </span>
  );
}
