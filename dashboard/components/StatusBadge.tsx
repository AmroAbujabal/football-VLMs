type Status = "pending" | "processing" | "done" | "failed" | string;

const dotClass: Record<string, string> = {
  done:       "dot-done",
  processing: "dot-processing",
  pending:    "dot-pending",
  failed:     "dot-failed",
};

const badgeClass: Record<string, string> = {
  done:       "badge-done",
  processing: "badge-processing",
  pending:    "badge-pending",
  failed:     "badge-failed",
};

export default function StatusBadge({ status }: { status: Status }) {
  const dot   = dotClass[status]   ?? "dot-pending";
  const badge = badgeClass[status] ?? "badge-pending";
  return (
    <span className={badge}>
      <span className={dot} aria-hidden="true" />
      {status}
    </span>
  );
}
