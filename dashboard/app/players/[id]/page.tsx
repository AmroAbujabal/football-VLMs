import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { api } from "@/lib/api";
import StatsHistoryChart from "@/components/StatsHistoryChart";

interface Props {
  params: { id: string };
}

function fmtDist(v: number | null) { return v != null ? `${Math.round(v)} m`       : "—"; }
function fmtSpd (v: number | null) { return v != null ? `${v.toFixed(2)} m/s`      : "—"; }
function fmtPct (v: number | null) { return v != null ? `${(v * 100).toFixed(1)}%` : "—"; }

// ── Metric pill ───────────────────────────────────────────────
function MetricPill({ label, value }: { label: string; value: string | number | null }) {
  const display = value ?? "—";
  return (
    <div className="flex flex-col gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-3">
      <p className="kpi-label">{label}</p>
      <p
        className="text-xl font-bold tabular-nums leading-none text-slate-800"
        style={{ fontFamily: "'Fira Code', monospace" }}
      >
        {display}
      </p>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────
export default async function PlayerProfilePage({ params }: Props) {
  let statsHistory;
  try {
    statsHistory = await api.players.stats(params.id);
  } catch {
    return (
      <main id="main-content" className="py-8">
        <div className="rounded-xl border border-red-200 bg-red-50 p-6">
          <p className="text-sm font-semibold text-red-700">Player not found or API unreachable</p>
          <Link href="/" className="mt-2 inline-block text-sm text-red-600 underline underline-offset-2">
            ← Back to matches
          </Link>
        </div>
      </main>
    );
  }

  const latest = statsHistory[0] ?? null;

  return (
    <main id="main-content" className="space-y-5">

      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-slate-400">
        <Link href="/" className="hover:text-slate-700 transition-colors">Matches</Link>
        <ChevronRight className="h-3 w-3" aria-hidden="true" />
        <span className="text-slate-700 font-medium">Player Profile</span>
      </nav>

      {/* Profile header */}
      <div className="card flex items-center gap-4">
        {/* Avatar */}
        <div
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl text-white"
          style={{ background: "linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%)" }}
          aria-hidden="true"
        >
          <span
            className="text-base font-bold"
            style={{ fontFamily: "'Fira Code', monospace" }}
          >#</span>
        </div>
        <div>
          <h1 className="text-base font-bold text-slate-900">Player Profile</h1>
          <p className="mt-0.5 text-xs text-slate-500">
            <span
              className="tabular-nums font-semibold text-slate-700"
              style={{ fontFamily: "'Fira Code', monospace" }}
            >
              {statsHistory.length}
            </span>
            {" "}
            match{statsHistory.length !== 1 ? "es" : ""} on record
          </p>
        </div>
      </div>

      {/* Latest match snapshot */}
      {latest && (
        <section aria-labelledby="latest-heading">
          <div className="mb-3">
            <h2 id="latest-heading" className="section-title">Latest match</h2>
            <p className="mt-0.5 text-xs text-slate-500">
              <span className="font-semibold text-home">{latest.home_team}</span>
              <span className="mx-1.5 text-slate-300">vs</span>
              <span className="font-semibold text-away">{latest.away_team}</span>
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricPill label="Distance"        value={fmtDist(latest.distance_covered_m)} />
            <MetricPill label="Top speed"       value={fmtSpd(latest.top_speed_ms)} />
            <MetricPill label="Avg speed"       value={fmtSpd(latest.avg_speed_ms)} />
            <MetricPill label="Sprints"         value={latest.sprint_count} />
            <MetricPill label="Hi-int. runs"    value={latest.hi_run_count} />
            <MetricPill label="Press count"     value={latest.press_count} />
            <MetricPill label="Press success"   value={fmtPct(latest.press_success_rate)} />
            <MetricPill label="Pitch control"   value={fmtPct(latest.pitch_control_contribution)} />
          </div>
        </section>
      )}

      {/* History chart */}
      <section aria-labelledby="chart-heading" className="card">
        <h2 id="chart-heading" className="section-title mb-4">Match history</h2>
        <StatsHistoryChart stats={statsHistory} />
        <p className="mt-3 text-center text-2xs text-slate-400">
          Distance (navy, left axis) · Sprints &amp; Presses (right axis) · last 8 matches
        </p>
      </section>

      {/* Full history table */}
      <section aria-labelledby="history-table-heading">
        <h2 id="history-table-heading" className="section-title mb-3">All matches</h2>
        <div className="overflow-x-auto rounded-[10px] border border-slate-200">
          <table className="data-table" aria-label="All match statistics">
            <thead>
              <tr>
                {["Match", "Team", "Distance", "Top Spd", "Sprints", "Presses", "Press %", "Pitch Ctrl"].map(
                  (h) => (
                    <th key={h} className="cursor-default">
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {statsHistory.map((s) => (
                <tr key={s.match_id}>
                  <td className="font-medium text-slate-900 whitespace-nowrap">
                    <Link
                      href={`/matches/${s.match_id}`}
                      className="hover:text-primary-700 hover:underline underline-offset-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 rounded"
                    >
                      {s.home_team} vs {s.away_team}
                    </Link>
                  </td>
                  <td>
                    <span className={s.team === "home" ? "team-pill-home" : "team-pill-away"}>
                      {s.team}
                    </span>
                  </td>
                  <td className="tabular-nums">{fmtDist(s.distance_covered_m)}</td>
                  <td className="tabular-nums">{fmtSpd(s.top_speed_ms)}</td>
                  <td className="tabular-nums">{s.sprint_count ?? "—"}</td>
                  <td className="tabular-nums">{s.press_count  ?? "—"}</td>
                  <td className="tabular-nums">{fmtPct(s.press_success_rate)}</td>
                  <td className="tabular-nums">{fmtPct(s.pitch_control_contribution)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
