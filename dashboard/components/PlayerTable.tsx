"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import type { MatchPlayer } from "@/lib/types";

type SortKey = keyof MatchPlayer;
type SortDir = "asc" | "desc";

function fmtNum(v: number | null, decimals = 1): string {
  return v == null ? "—" : v.toFixed(decimals);
}
function fmtPct(v: number | null): string {
  return v == null ? "—" : `${(v * 100).toFixed(0)}%`;
}

const COLS: {
  key: SortKey;
  label: string;
  render: (p: MatchPlayer) => string;
}[] = [
  { key: "player_name",              label: "Player",     render: (p) => p.player_name },
  { key: "team",                     label: "Team",       render: (p) => p.team },
  { key: "distance_covered_m",       label: "Dist (m)",   render: (p) => fmtNum(p.distance_covered_m, 0) },
  { key: "top_speed_ms",             label: "Top Spd",    render: (p) => fmtNum(p.top_speed_ms) },
  { key: "avg_speed_ms",             label: "Avg Spd",    render: (p) => fmtNum(p.avg_speed_ms) },
  { key: "sprint_count",             label: "Sprints",    render: (p) => fmtNum(p.sprint_count, 0) },
  { key: "hi_run_count",             label: "Hi-Runs",    render: (p) => fmtNum(p.hi_run_count, 0) },
  { key: "press_count",              label: "Presses",    render: (p) => fmtNum(p.press_count, 0) },
  { key: "press_success_rate",       label: "Press %",    render: (p) => fmtPct(p.press_success_rate) },
  { key: "pitch_control_contribution", label: "Pitch Ctrl", render: (p) => fmtPct(p.pitch_control_contribution) },
];

function SortIcon({ col, sortKey, dir }: { col: SortKey; sortKey: SortKey; dir: SortDir }) {
  if (col !== sortKey) return <ArrowUpDown className="ml-1 inline h-3 w-3 opacity-30" aria-hidden="true" />;
  return dir === "asc"
    ? <ArrowUp   className="ml-1 inline h-3 w-3 text-primary-700" aria-hidden="true" />
    : <ArrowDown className="ml-1 inline h-3 w-3 text-primary-700" aria-hidden="true" />;
}

export default function PlayerTable({ players }: { players: MatchPlayer[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("team");
  const [dir, setDir]         = useState<SortDir>("asc");

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setDir("desc"); // numeric cols start descending
    }
  }

  const sorted = [...players].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    if (av == null) return 1;
    if (bv == null) return -1;
    const cmp = av < bv ? -1 : av > bv ? 1 : 0;
    return dir === "asc" ? cmp : -cmp;
  });

  return (
    <div className="overflow-x-auto rounded-[10px] border border-slate-200">
      <table className="data-table" aria-label="Player statistics">
        <thead>
          <tr>
            {COLS.map((c) => (
              <th
                key={c.key}
                onClick={() => handleSort(c.key)}
                aria-sort={
                  sortKey === c.key
                    ? dir === "asc" ? "ascending" : "descending"
                    : "none"
                }
              >
                {c.label}
                <SortIcon col={c.key} sortKey={sortKey} dir={dir} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((p) => (
            <tr key={p.player_id}>
              {/* Player name — linked */}
              <td className="font-medium text-slate-900 whitespace-nowrap">
                <Link
                  href={`/players/${p.player_id}`}
                  className="hover:text-primary-700 hover:underline underline-offset-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 rounded"
                >
                  {p.player_name}
                </Link>
              </td>

              {/* Team */}
              <td>
                <span className={p.team === "home" ? "team-pill-home" : "team-pill-away"}>
                  {p.team}
                </span>
              </td>

              {/* Numeric columns */}
              <td className="tabular-nums">{fmtNum(p.distance_covered_m, 0)}</td>
              <td className="tabular-nums">{fmtNum(p.top_speed_ms)}</td>
              <td className="tabular-nums">{fmtNum(p.avg_speed_ms)}</td>
              <td className="tabular-nums">{fmtNum(p.sprint_count, 0)}</td>
              <td className="tabular-nums">{fmtNum(p.hi_run_count, 0)}</td>
              <td className="tabular-nums">{fmtNum(p.press_count, 0)}</td>
              <td className="tabular-nums">{fmtPct(p.press_success_rate)}</td>
              <td className="tabular-nums">{fmtPct(p.pitch_control_contribution)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
