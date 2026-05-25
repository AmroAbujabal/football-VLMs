// ---------------------------------------------------------------------------
// Mirrors the Pydantic response schemas in api/schemas/__init__.py
// and api/routers/matches.py MatchListResponse
// ---------------------------------------------------------------------------

export interface MatchListItem {
  id: string;
  home_team: string;
  away_team: string;
  match_date: string | null;
  processing_status: "pending" | "processing" | "done" | "failed";
  created_at: string;
}

export interface MatchSummary {
  match_id: string;
  home_team: string;
  away_team: string;
  processing_status: string;
  player_count: number;
  home_pitch_control_pct: number;
  away_pitch_control_pct: number;
  home_top_speed_ms: number;
  away_top_speed_ms: number;
  home_press_count: number;
  away_press_count: number;
}

export interface MatchPlayer {
  player_id: string;
  player_name: string;
  team: "home" | "away";
  distance_covered_m: number | null;
  top_speed_ms: number | null;
  avg_speed_ms: number | null;
  sprint_count: number | null;
  hi_run_count: number | null;
  press_count: number | null;
  press_success_rate: number | null;
  pitch_control_contribution: number | null;
}

export interface PlayerStats {
  match_id: string;
  home_team: string;
  away_team: string;
  team: string;
  distance_covered_m: number | null;
  top_speed_ms: number | null;
  avg_speed_ms: number | null;
  sprint_count: number | null;
  hi_run_count: number | null;
  press_count: number | null;
  press_success_rate: number | null;
  pitch_control_contribution: number | null;
}
