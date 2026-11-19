export const RECEIVABLES_CHANGED = "recovra:receivables-changed";

/** Call after import accept or when an existing invoice is linked on duplicate. */
export function notifyReceivablesChanged(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(RECEIVABLES_CHANGED));
  }
}