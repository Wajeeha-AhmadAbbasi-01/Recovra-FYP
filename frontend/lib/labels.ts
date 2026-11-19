export const IMPORT_STATUS_LABELS: Record<string, string> = {
  ACCEPTED_LOCAL_CHECK: "Accepted — local format check passed",
  REJECTED_LOCAL_CHECK: "Rejected — format check failed",
  NEEDS_MANUAL_REVIEW: "Needs manual review",
  REJECTED_UNSUPPORTED: "Unsupported file",
  DUPLICATE: "Already imported / duplicate",
  PROCESSING_ERROR: "Processing error",
};

export function importStatusLabel(status: string): string {
  return IMPORT_STATUS_LABELS[status] ?? status.replace(/_/g, " ").toLowerCase();
}

export function isImportAccepted(status: string): boolean {
  return status === "ACCEPTED_LOCAL_CHECK";
}

export function isImportDuplicate(status: string): boolean {
  return status === "DUPLICATE";
}

export function isImportRejected(status: string): boolean {
  return (
    status === "REJECTED_LOCAL_CHECK" ||
    status === "REJECTED_UNSUPPORTED" ||
    status === "PROCESSING_ERROR"
  );
}