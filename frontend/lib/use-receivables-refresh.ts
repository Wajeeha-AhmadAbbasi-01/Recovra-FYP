"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { RECEIVABLES_CHANGED } from "@/lib/receivables-events";

/**
 * Refetch receivables data on mount, pathname change, tab focus, and after PDF import.
 */
export function useReceivablesRefresh(load: () => void | Promise<void>, deps: unknown[] = []): void {
  const pathname = usePathname();
  const loadRef = useRef(load);
  loadRef.current = load;

  useEffect(() => {
    const run = () => {
      void loadRef.current();
    };
    run();
    const onImport = () => run();
    const onVisible = () => {
      if (document.visibilityState === "visible") run();
    };
    window.addEventListener(RECEIVABLES_CHANGED, onImport);
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.removeEventListener(RECEIVABLES_CHANGED, onImport);
      document.removeEventListener("visibilitychange", onVisible);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname, ...deps]);
}