"use client";

import { useState } from "react";
import type { ImportIssue } from "@/lib/labels";

function issueList(issues: unknown): ImportIssue[] {
  if (!Array.isArray(issues)) return [];
  return issues.filter((i): i is ImportIssue => typeof i === "object" && i !== null);
}

export function ImportFindings({
  issues,
  warnings,
}: {
  issues: unknown;
  warnings: unknown;
}) {
  const [open, setOpen] = useState(false);
  const err = issueList(issues);
  const warn = issueList(warnings);
  if (!err.length && !warn.length) return <span className="text-muted">—</span>;

  const preview = [...err, ...warn]
    .map((i) => i.message)
    .filter(Boolean)
    .slice(0, 2)
    .join("; ");

  return (
    <div className="max-w-xs text-xs">
      <p className="text-muted">{preview || "See details"}</p>
      {(err.length > 2 || warn.length > 0 || err.some((i) => i.rule_id)) && (
        <button
          type="button"
          className="mt-1 font-medium text-accent hover:underline"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? "Hide findings" : "Show findings"}
        </button>
      )}
      {open ? (
        <ul className="mt-2 space-y-2 rounded-lg border border-border bg-canvas p-2 text-left">
          {err.map((i, idx) => (
            <li key={`e-${idx}`}>
              <span className="font-medium text-danger">{i.severity ?? "ERROR"}</span>
              {i.rule_id ? <span className="ml-1 font-mono text-[10px] text-muted">{i.rule_id}</span> : null}
              <p className="mt-0.5">{i.message}</p>
              {i.field ? <p className="text-[10px] text-muted">Field: {i.field}</p> : null}
            </li>
          ))}
          {warn.map((i, idx) => (
            <li key={`w-${idx}`}>
              <span className="font-medium text-warning">{i.severity ?? "WARNING"}</span>
              {i.rule_id ? <span className="ml-1 font-mono text-[10px] text-muted">{i.rule_id}</span> : null}
              <p className="mt-0.5">{i.message}</p>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}