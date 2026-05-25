import { api } from "@/lib/api";
import MatchCard from "@/components/MatchCard";

const ACADEMY_ID = process.env.NEXT_PUBLIC_ACADEMY_ID ?? "";

export default async function HomePage() {
  if (!ACADEMY_ID) {
    return (
      <main id="main-content" className="flex flex-col items-center justify-center py-32 text-center">
        <div className="rounded-xl border border-slate-200 bg-white px-10 py-12 shadow-card max-w-md">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary-50">
            <svg className="h-6 w-6 text-primary-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
          </div>
          <h1 className="mb-2 text-base font-semibold text-slate-800">No academy configured</h1>
          <p className="text-sm text-slate-500 leading-relaxed">
            Set{" "}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-mono text-primary-700">
              NEXT_PUBLIC_ACADEMY_ID
            </code>{" "}
            in your{" "}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-mono text-slate-700">
              .env.local
            </code>{" "}
            to a valid academy UUID from the database.
          </p>
        </div>
      </main>
    );
  }

  let matches;
  try {
    matches = await api.matches.list(ACADEMY_ID);
  } catch {
    return (
      <main id="main-content" className="py-8">
        <div className="rounded-xl border border-red-200 bg-red-50 p-6">
          <p className="text-sm font-semibold text-red-700">Could not reach the API</p>
          <p className="mt-1 text-sm text-red-600">
            Make sure the FastAPI server is running on{" "}
            <code className="rounded bg-red-100 px-1 py-0.5 font-mono text-xs">
              {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
            </code>
          </p>
        </div>
      </main>
    );
  }

  const done       = matches.filter((m) => m.processing_status === "done").length;
  const processing = matches.filter((m) => m.processing_status === "processing").length;

  return (
    <main id="main-content">
      {/* Page header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Matches</h1>
          <p className="mt-0.5 text-sm text-slate-500">
            {matches.length} total
            {done > 0       && <> · <span className="text-emerald-600 font-medium">{done} analysed</span></>}
            {processing > 0 && <> · <span className="text-amber-600 font-medium">{processing} processing</span></>}
          </p>
        </div>
      </div>

      {matches.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-20 text-center">
          <p className="text-sm font-medium text-slate-400">No matches yet</p>
          <p className="mt-1 text-xs text-slate-300">Upload a video to begin analysis</p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {matches.map((m) => (
            <MatchCard key={m.id} match={m} />
          ))}
        </div>
      )}
    </main>
  );
}
