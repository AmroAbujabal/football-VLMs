interface Props {
  homePct: number; // 0–1
  awayPct: number; // 0–1
  homeTeam: string;
  awayTeam: string;
}

export default function PitchControlBar({
  homePct,
  awayPct,
  homeTeam,
  awayTeam,
}: Props) {
  const total  = homePct + awayPct || 1;
  const homeW  = Math.round((homePct / total) * 100);
  const awayW  = 100 - homeW;
  const homeFmt = (homePct * 100).toFixed(1);
  const awayFmt = (awayPct * 100).toFixed(1);

  return (
    <div
      role="img"
      aria-label={`Pitch control: ${homeTeam} ${homeFmt}%, ${awayTeam} ${awayFmt}%`}
    >
      {/* Labels row */}
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-home" aria-hidden="true" />
          <span className="text-xs font-medium text-slate-600">{homeTeam}</span>
        </div>
        <span className="kpi-label">Pitch Control</span>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate-600">{awayTeam}</span>
          <span className="h-2 w-2 rounded-full bg-away" aria-hidden="true" />
        </div>
      </div>

      {/* Bar */}
      <div className="flex h-6 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="flex items-center justify-end pr-2.5 bg-home transition-all duration-500"
          style={{ width: `${homeW}%` }}
        >
          <span
            className="text-2xs font-bold text-white tabular-nums"
            style={{ fontFamily: "'Fira Code', monospace" }}
          >
            {homeFmt}%
          </span>
        </div>
        <div
          className="flex items-center justify-start pl-2.5 bg-away transition-all duration-500"
          style={{ width: `${awayW}%` }}
        >
          <span
            className="text-2xs font-bold text-white tabular-nums"
            style={{ fontFamily: "'Fira Code', monospace" }}
          >
            {awayFmt}%
          </span>
        </div>
      </div>
    </div>
  );
}
