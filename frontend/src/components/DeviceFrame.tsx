import type { ReactNode } from "react";

export type DeviceKind = "phone" | "tablet" | "desktop";

const SIZES: Record<DeviceKind, { w: number; h: number; bezel: string }> = {
  phone: { w: 390, h: 844, bezel: "rounded-[36px] border-[10px] border-neutral-800" },
  tablet: { w: 820, h: 1180, bezel: "rounded-[24px] border-[12px] border-neutral-800" },
  desktop: { w: 1280, h: 800, bezel: "rounded-md border border-neutral-800" },
};

interface Props {
  device: DeviceKind;
  children: ReactNode;
}

export function DeviceFrame({ device, children }: Props): JSX.Element {
  const { w, h, bezel } = SIZES[device];
  return (
    <div className="flex w-full justify-center">
      <div
        className={`overflow-hidden bg-white shadow-2xl ${bezel}`}
        style={{ width: w, height: h, maxWidth: "100%" }}
      >
        {children}
      </div>
    </div>
  );
}
