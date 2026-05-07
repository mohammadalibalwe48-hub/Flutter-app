import { useEffect, useRef } from "react";

interface Props {
  text: string;
}

export function BuildLog({ text }: Props): JSX.Element {
  const ref = useRef<HTMLPreElement | null>(null);
  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [text]);
  return (
    <pre
      ref={ref}
      className="h-72 overflow-auto rounded border border-neutral-800 bg-black p-3 font-mono text-xs leading-relaxed text-neutral-300"
    >
      {text || "(no logs yet)"}
    </pre>
  );
}
