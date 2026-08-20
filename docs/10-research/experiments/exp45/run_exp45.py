"""EXP-45: Condensation retention and consequential loss in longitudinal transcripts.

Protocol pre-registered in docs/10-research/experiment-register.md § EXP-45.
Evaluates:
1. Condensation frequency and session longevity across longitudinal transcripts.
2. Item retention rate across condensation boundaries (beta analogue).
3. Consequential loss rate (loss-that-bit: file re-reads, repeated discovery commands).
4. Predictors of survival (recency, frequency, tool vs prose origin, acted-upon).
5. Pre-registered stopping rule evaluations.

Privacy rule: Purely aggregate statistics. No private code, paths, or message excerpts.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Regex for file paths (relative or absolute)
PATH_RE = re.compile(r"(?:[a-zA-Z0-9_\-\.]+[/\\])+[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+")
# Regex for identifiers (length >= 4)
IDENT_RE = re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_]{3,}\b")


# --- Statistical Helpers ---


def percentile(arr: List[float], p: float) -> float:
    """Compute linear percentile p in [0, 100]."""
    if not arr:
        return 0.0
    s = sorted(arr)
    n = len(s)
    if n == 1:
        return float(s[0])
    k = (n - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(s[int(k)])
    d0 = s[int(f)] * (c - k)
    d1 = s[int(c)] * (k - f)
    return float(d0 + d1)


def bootstrap_ci(
    arr: List[float],
    stat_fn: Any = statistics.mean,
    n_boot: int = 2000,
    ci: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float]:
    """Compute bootstrap confidence interval for a statistic."""
    if not arr:
        return (0.0, 0.0)
    if len(arr) == 1:
        val = float(stat_fn(arr))
        return (val, val)
    rng = random.Random(seed)
    n = len(arr)
    boot_stats = []
    for _ in range(n_boot):
        sample = [arr[rng.randint(0, n - 1)] for _ in range(n)]
        boot_stats.append(stat_fn(sample))
    alpha = (1.0 - ci) / 2.0
    low = percentile(boot_stats, alpha * 100.0)
    high = percentile(boot_stats, (1.0 - alpha) * 100.0)
    return (round(low, 4), round(high, 4))


def rank_data(arr: List[float]) -> List[float]:
    """Compute fractional ranks for ties."""
    n = len(arr)
    indexed = sorted(enumerate(arr), key=lambda x: x[1])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n - 1 and indexed[j][1] == indexed[j + 1][1]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def spearman_rho(x: List[float], y: List[float]) -> float:
    """Compute Spearman rank correlation between two vectors."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    rx = rank_data(x)
    ry = rank_data(y)
    mean_rx = statistics.mean(rx)
    mean_ry = statistics.mean(ry)

    nom = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(len(rx)))
    den_x = sum((rx[i] - mean_rx) ** 2 for i in range(len(rx)))
    den_y = sum((ry[i] - mean_ry) ** 2 for i in range(len(ry)))
    if den_x <= 0 or den_y <= 0:
        return 0.0
    return round(nom / math.sqrt(den_x * den_y), 4)


def point_biserial_r(continuous: List[float], binary: List[int]) -> float:
    """Compute point-biserial correlation between continuous feature and binary target."""
    if len(continuous) != len(binary) or len(continuous) < 2:
        return 0.0
    n0 = sum(1 for b in binary if b == 0)
    n1 = sum(1 for b in binary if b == 1)
    if n0 == 0 or n1 == 0:
        return 0.0
    n = len(binary)
    vals0 = [continuous[i] for i in range(n) if binary[i] == 0]
    vals1 = [continuous[i] for i in range(n) if binary[i] == 1]
    m0 = statistics.mean(vals0)
    m1 = statistics.mean(vals1)
    stdev = statistics.stdev(continuous) if n > 1 else 0.0
    if stdev == 0.0:
        return 0.0
    r_pb = ((m1 - m0) / stdev) * math.sqrt((n0 * n1) / (n * (n - 1)))
    return round(r_pb, 4)


# --- Data Structures & Entity Extraction ---


@dataclass
class EntityRecord:
    name: str
    kind: str  # "path", "ident", "command"
    turn_idx: int
    is_tool_origin: bool
    is_acted_upon: bool


@dataclass
class BoundaryEvent:
    session_id: str
    boundary_type: str  # "compact_boundary" or "away_summary"
    record_index: int
    turn_index: int
    pre_tokens: Optional[int] = None
    post_tokens: Optional[int] = None
    dropped_tokens: Optional[int] = None
    trigger: Optional[str] = None


@dataclass
class BoundaryAnalysis:
    boundary: BoundaryEvent
    pre_entities_count: int
    post_entities_count: int
    retained_entities_count: int
    retention_rate: float
    # Stratified retention
    path_retention_rate: float
    ident_retention_rate: float
    # Consequential loss
    pre_read_files_count: int
    post_reread_files_count: int
    reread_rate: float
    pre_discovery_commands_count: int
    post_re_discovery_commands_count: int
    rediscovery_rate: float
    consequential_loss_rate: float


def normalize_path(p: str) -> str:
    """Normalize file path for exact matching."""
    clean = p.replace("\\", "/").strip().strip("'\"`")
    if clean.startswith("./"):
        clean = clean[2:]
    return clean


def extract_record_entities(
    record: Dict[str, Any], turn_idx: int
) -> Tuple[List[EntityRecord], Set[str], Set[str]]:
    """Extract entities, read file paths, and discovery commands from a record."""
    entities: List[EntityRecord] = []
    read_files: Set[str] = set()
    discovery_commands: Set[str] = set()

    t = record.get("type")
    msg = record.get("message")

    # Determine origin channel
    is_tool_origin = (t == "user" and isinstance(msg, dict) and any(
        isinstance(item, dict) and item.get("type") == "tool_result"
        for item in (msg.get("content") if isinstance(msg.get("content"), list) else [])
    ))

    texts_for_scan: List[str] = []

    if isinstance(msg, dict):
        content = msg.get("content")
        if isinstance(content, str):
            texts_for_scan.append(content)
        elif isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                itype = item.get("type")
                if itype == "text":
                    texts_for_scan.append(item.get("text", ""))
                elif itype == "tool_use":
                    tname = item.get("name", "")
                    inp = item.get("input", {})
                    if isinstance(inp, dict):
                        # File operations
                        if tname in ("Read", "Edit", "Write", "View"):
                            p = inp.get("file_path") or inp.get("path") or inp.get("target_file")
                            if p and isinstance(p, str):
                                norm_p = normalize_path(p)
                                entities.append(
                                    EntityRecord(
                                        name=norm_p,
                                        kind="path",
                                        turn_idx=turn_idx,
                                        is_tool_origin=False,
                                        is_acted_upon=True,
                                    )
                                )
                                if tname in ("Read", "View"):
                                    read_files.add(norm_p)
                        # Bash commands
                        elif tname == "Bash":
                            cmd = inp.get("command")
                            if cmd and isinstance(cmd, str):
                                # Extract root command / discovery patterns
                                first_word = cmd.strip().split()[0] if cmd.strip() else ""
                                entities.append(
                                    EntityRecord(
                                        name=first_word,
                                        kind="command",
                                        turn_idx=turn_idx,
                                        is_tool_origin=False,
                                        is_acted_upon=True,
                                    )
                                )
                                if first_word in ("grep", "rg", "find", "ls", "git", "pytest", "which"):
                                    # Normalize discovery command signature
                                    norm_cmd = " ".join(cmd.strip().split())
                                    discovery_commands.add(norm_cmd)
                                texts_for_scan.append(cmd)
                        # General tool inputs
                        for val in inp.values():
                            if isinstance(val, str):
                                texts_for_scan.append(val)
                elif itype == "tool_result":
                    res_content = item.get("content", "")
                    if isinstance(res_content, str):
                        texts_for_scan.append(res_content)
                    elif isinstance(res_content, list):
                        for sub in res_content:
                            if isinstance(sub, dict) and sub.get("type") == "text":
                                texts_for_scan.append(sub.get("text", ""))

    elif isinstance(msg, str):
        texts_for_scan.append(msg)

    # Extract regex identifiers and paths from gathered texts
    for txt in texts_for_scan:
        for p in PATH_RE.findall(txt):
            norm_p = normalize_path(p)
            entities.append(
                EntityRecord(
                    name=norm_p,
                    kind="path",
                    turn_idx=turn_idx,
                    is_tool_origin=is_tool_origin,
                    is_acted_upon=False,
                )
            )
        for ident in IDENT_RE.findall(txt):
            entities.append(
                EntityRecord(
                    name=ident,
                    kind="ident",
                    turn_idx=turn_idx,
                    is_tool_origin=is_tool_origin,
                    is_acted_upon=False,
                )
            )

    return entities, read_files, discovery_commands


# --- Session Processing & Analysis ---


def parse_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    if not ts_str:
        return None
    try:
        clean = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except Exception:
        return None


def analyze_transcript_file(file_path: Path) -> Dict[str, Any]:
    """Parse and extract metadata, records, and boundaries from a single JSONL file."""
    records: List[Dict[str, Any]] = []
    session_id: Optional[str] = None
    timestamps: List[datetime] = []
    boundaries: List[BoundaryEvent] = []

    turn_count = 0

    with open(file_path, "r", encoding="utf-8", errors="replace") as fp:
        for line_idx, line in enumerate(fp):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue

            records.append(obj)
            if not session_id:
                session_id = obj.get("sessionId")

            t = obj.get("type")
            sub = obj.get("subtype")

            if t in ("user", "assistant"):
                turn_count += 1

            ts = parse_timestamp(obj.get("timestamp"))
            if ts:
                timestamps.append(ts)

            if t == "system" and sub in ("compact_boundary", "away_summary"):
                meta = obj.get("compactMetadata", {})
                boundaries.append(
                    BoundaryEvent(
                        session_id=session_id or str(file_path.name),
                        boundary_type=sub,
                        record_index=len(records) - 1,
                        turn_index=turn_count,
                        pre_tokens=meta.get("preTokens"),
                        post_tokens=meta.get("postTokens"),
                        dropped_tokens=meta.get("cumulativeDroppedTokens"),
                        trigger=meta.get("trigger"),
                    )
                )

    duration_days = 0.0
    if len(timestamps) >= 2:
        duration_days = (timestamps[-1] - timestamps[0]).total_seconds() / 86400.0

    return {
        "file_name": file_path.name,
        "session_id": session_id or str(file_path.name),
        "records_count": len(records),
        "turns_count": turn_count,
        "duration_days": duration_days,
        "timestamps": timestamps,
        "boundaries": boundaries,
        "records": records,
    }


def analyze_boundary_retention(
    records: List[Dict[str, Any]], boundary: BoundaryEvent
) -> Tuple[BoundaryAnalysis, List[Dict[str, Any]]]:
    """Compute retention, consequential loss, and entity-level survival features for a boundary."""
    b_rec_idx = boundary.record_index
    b_turn_idx = boundary.turn_index

    pre_records = records[:b_rec_idx]
    post_records = records[b_rec_idx + 1:]

    # Entity maps: name -> list of EntityRecords
    pre_entity_map: Dict[Tuple[str, str], List[EntityRecord]] = defaultdict(list)
    pre_read_files: Set[str] = set()
    pre_discovery_commands: Set[str] = set()

    turn_counter = 0
    for r in pre_records:
        if r.get("type") in ("user", "assistant"):
            turn_counter += 1
        ents, rfiles, dcmds = extract_record_entities(r, turn_counter)
        for e in ents:
            pre_entity_map[(e.name, e.kind)].append(e)
        pre_read_files.update(rfiles)
        pre_discovery_commands.update(dcmds)

    post_entity_set: Set[Tuple[str, str]] = set()
    post_read_files: Set[str] = set()
    post_discovery_commands: Set[str] = set()

    for r in post_records:
        if r.get("type") in ("user", "assistant"):
            turn_counter += 1
        ents, rfiles, dcmds = extract_record_entities(r, turn_counter)
        for e in ents:
            post_entity_set.add((e.name, e.kind))
        post_read_files.update(rfiles)
        post_discovery_commands.update(dcmds)

    # Compute retention
    pre_keys = set(pre_entity_map.keys())
    retained_keys = pre_keys & post_entity_set
    lost_keys = pre_keys - post_entity_set

    retention_rate = len(retained_keys) / max(1, len(pre_keys))

    # Stratified retention
    pre_paths = {k[0] for k in pre_keys if k[1] == "path"}
    post_paths = {k[0] for k in post_entity_set if k[1] == "path"}
    path_retention = len(pre_paths & post_paths) / max(1, len(pre_paths))

    pre_idents = {k[0] for k in pre_keys if k[1] == "ident"}
    post_idents = {k[0] for k in post_entity_set if k[1] == "ident"}
    ident_retention = len(pre_idents & post_idents) / max(1, len(pre_idents))

    # Consequential loss: pre-read files re-read post-boundary
    reread_files = pre_read_files & post_read_files
    reread_rate = len(reread_files) / max(1, len(pre_read_files))

    # Discovery commands re-executed post-boundary
    rediscovery_commands = pre_discovery_commands & post_discovery_commands
    rediscovery_rate = len(rediscovery_commands) / max(1, len(pre_discovery_commands))

    # Total consequential loss events over lost entities
    consequential_events = len(reread_files) + len(rediscovery_commands)
    consequential_loss_rate = consequential_events / max(1, len(lost_keys))

    analysis = BoundaryAnalysis(
        boundary=boundary,
        pre_entities_count=len(pre_keys),
        post_entities_count=len(post_entity_set),
        retained_entities_count=len(retained_keys),
        retention_rate=retention_rate,
        path_retention_rate=path_retention,
        ident_retention_rate=ident_retention,
        pre_read_files_count=len(pre_read_files),
        post_reread_files_count=len(reread_files),
        reread_rate=reread_rate,
        pre_discovery_commands_count=len(pre_discovery_commands),
        post_re_discovery_commands_count=len(rediscovery_commands),
        rediscovery_rate=rediscovery_rate,
        consequential_loss_rate=consequential_loss_rate,
    )

    # Feature extraction for survival prediction
    survival_rows: List[Dict[str, Any]] = []
    for (name, kind), occurrences in pre_entity_map.items():
        survived = 1 if (name, kind) in post_entity_set else 0
        freq = len(occurrences)
        # Recency: distance in turns from last occurrence to boundary
        last_turn = max(occ.turn_idx for occ in occurrences)
        recency_turn_dist = max(0, b_turn_idx - last_turn)
        # Tool origin fraction
        tool_origin_frac = sum(1 for occ in occurrences if occ.is_tool_origin) / freq
        # Acted upon
        is_acted = 1 if any(occ.is_acted_upon for occ in occurrences) else 0

        survival_rows.append(
            {
                "survived": survived,
                "frequency": float(freq),
                "recency_turn_dist": float(recency_turn_dist),
                "tool_origin_frac": float(tool_origin_frac),
                "is_acted_upon": float(is_acted),
                "is_path": 1.0 if kind == "path" else 0.0,
                "is_ident": 1.0 if kind == "ident" else 0.0,
            }
        )

    return analysis, survival_rows


# --- Corpus-Level Runner ---


def run_exp45_analysis(
    corpus_dir: Path, output_json_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Execute complete EXP-45 measurement protocol."""
    jsonl_files = sorted(corpus_dir.rglob("*.jsonl"))
    total_files = len(jsonl_files)

    if total_files == 0:
        return {
            "verdict": "insufficient_evidence",
            "reason": f"No JSONL transcript files found in {corpus_dir}",
        }

    # Group files by sessionId
    session_records_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    session_durations: Dict[str, float] = {}
    session_turn_counts: Dict[str, int] = defaultdict(int)
    all_boundaries: List[Tuple[BoundaryEvent, List[Dict[str, Any]]]] = []

    file_level_durations: List[float] = []
    file_level_records: List[int] = []
    file_level_turns: List[int] = []

    for fpath in jsonl_files:
        res = analyze_transcript_file(fpath)
        file_level_durations.append(res["duration_days"])
        file_level_records.append(res["records_count"])
        file_level_turns.append(res["turns_count"])

        sid = res["session_id"]
        session_records_map[sid].extend(res["records"])
        session_turn_counts[sid] += res["turns_count"]
        session_durations[sid] = max(session_durations.get(sid, 0.0), res["duration_days"])

        for b in res["boundaries"]:
            all_boundaries.append((b, res["records"]))

    total_sessions = len(session_records_map)
    compact_boundary_events = [b for b, _ in all_boundaries if b.boundary_type == "compact_boundary"]
    away_summary_events = [b for b, _ in all_boundaries if b.boundary_type == "away_summary"]

    sessions_with_compact = {b.session_id for b in compact_boundary_events}
    sessions_with_away = {b.session_id for b in away_summary_events}
    sessions_with_any_boundary = sessions_with_compact | sessions_with_away

    # 1. Frequency and Longevity
    longevity_summary = {
        "total_files": total_files,
        "total_unique_sessions": total_sessions,
        "sessions_with_compact_boundary": len(sessions_with_compact),
        "total_compact_boundary_events": len(compact_boundary_events),
        "sessions_with_away_summary": len(sessions_with_away),
        "total_away_summary_events": len(away_summary_events),
        "sessions_with_any_boundary": len(sessions_with_any_boundary),
        "total_all_boundary_events": len(all_boundaries),
        "record_counts": {
            "p50": round(percentile([float(r) for r in file_level_records], 50), 1),
            "p90": round(percentile([float(r) for r in file_level_records], 90), 1),
            "p95": round(percentile([float(r) for r in file_level_records], 95), 1),
            "p99": round(percentile([float(r) for r in file_level_records], 99), 1),
            "max": max(file_level_records) if file_level_records else 0,
        },
        "duration_days": {
            "p50": round(percentile(file_level_durations, 50), 4),
            "p90": round(percentile(file_level_durations, 90), 4),
            "p95": round(percentile(file_level_durations, 95), 4),
            "p99": round(percentile(file_level_durations, 99), 4),
            "max": round(max(file_level_durations), 4) if file_level_durations else 0.0,
        },
        "session_level_duration_days_max": round(max(session_durations.values()), 4) if session_durations else 0.0,
    }

    # 2 & 3. Boundary Analyses (Retention and Consequential Loss)
    boundary_analyses: List[BoundaryAnalysis] = []
    all_survival_rows: List[Dict[str, Any]] = []

    for b, recs in all_boundaries:
        b_analysis, s_rows = analyze_boundary_retention(recs, b)
        boundary_analyses.append(b_analysis)
        all_survival_rows.extend(s_rows)

    compact_analyses = [ba for ba in boundary_analyses if ba.boundary.boundary_type == "compact_boundary"]
    away_analyses = [ba for ba in boundary_analyses if ba.boundary.boundary_type == "away_summary"]

    retention_rates_all = [ba.retention_rate for ba in boundary_analyses]
    path_retention_all = [ba.path_retention_rate for ba in boundary_analyses]
    ident_retention_all = [ba.ident_retention_rate for ba in boundary_analyses]

    retention_rates_compact = [ba.retention_rate for ba in compact_analyses]
    retention_rates_away = [ba.retention_rate for ba in away_analyses]

    # Consequential loss metrics
    reread_rates_all = [ba.reread_rate for ba in boundary_analyses if ba.pre_read_files_count > 0]
    consequential_loss_rates_all = [ba.consequential_loss_rate for ba in boundary_analyses]

    total_pre_read = sum(ba.pre_read_files_count for ba in boundary_analyses)
    total_post_reread = sum(ba.post_reread_files_count for ba in boundary_analyses)
    aggregate_file_reread_rate = total_post_reread / max(1, total_pre_read)

    total_pre_discovery = sum(ba.pre_discovery_commands_count for ba in boundary_analyses)
    total_post_rediscovery = sum(ba.post_re_discovery_commands_count for ba in boundary_analyses)
    aggregate_rediscovery_rate = total_post_rediscovery / max(1, total_pre_discovery)

    total_lost_entities = sum(ba.pre_entities_count - ba.retained_entities_count for ba in boundary_analyses)
    total_consequential_events = total_post_reread + total_post_rediscovery
    aggregate_consequential_loss_rate = total_consequential_events / max(1, total_lost_entities)

    retention_summary = {
        "all_boundaries_count": len(boundary_analyses),
        "mean_retention_rate": round(statistics.mean(retention_rates_all), 4) if retention_rates_all else 0.0,
        "retention_bootstrap_95ci": list(bootstrap_ci(retention_rates_all)),
        "path_retention_mean": round(statistics.mean(path_retention_all), 4) if path_retention_all else 0.0,
        "ident_retention_mean": round(statistics.mean(ident_retention_all), 4) if ident_retention_all else 0.0,
        "compact_boundary_mean_retention": round(statistics.mean(retention_rates_compact), 4) if retention_rates_compact else 0.0,
        "away_summary_mean_retention": round(statistics.mean(retention_rates_away), 4) if retention_rates_away else 0.0,
    }

    consequential_loss_summary = {
        "mean_consequential_loss_rate": round(statistics.mean(consequential_loss_rates_all), 4) if consequential_loss_rates_all else 0.0,
        "aggregate_file_reread_rate": round(aggregate_file_reread_rate, 4),
        "total_pre_read_files": total_pre_read,
        "total_reread_files": total_post_reread,
        "aggregate_command_rediscovery_rate": round(aggregate_rediscovery_rate, 4),
        "total_pre_discovery_commands": total_pre_discovery,
        "total_rediscovery_commands": total_post_rediscovery,
        "aggregate_consequential_loss_rate": round(aggregate_consequential_loss_rate, 4),
    }

    # 4. Survival Predictor Correlations
    survival_correlations = {}
    if all_survival_rows:
        survived = [int(r["survived"]) for r in all_survival_rows]
        features = [
            ("frequency", [r["frequency"] for r in all_survival_rows]),
            ("recency_turn_dist", [r["recency_turn_dist"] for r in all_survival_rows]),
            ("tool_origin_frac", [r["tool_origin_frac"] for r in all_survival_rows]),
            ("is_acted_upon", [r["is_acted_upon"] for r in all_survival_rows]),
            ("is_path", [r["is_path"] for r in all_survival_rows]),
            ("is_ident", [r["is_ident"] for r in all_survival_rows]),
        ]

        for fname, fvals in features:
            rho = spearman_rho(fvals, [float(s) for s in survived])
            r_pb = point_biserial_r(fvals, survived)
            survival_correlations[fname] = {
                "spearman_rho": rho,
                "point_biserial_r": r_pb,
            }

    # 5. Pre-registered Stopping Rules Evaluation
    # Rule 1: R >= 98% -> near-lossless
    # Rule 2: R < 98% and L_bite < 1.0% -> loss does not bite
    # Rule 3: R < 98% and L_bite >= 1.0% -> verifier with bite
    # Rule 4: < 10 condensed sessions -> insufficient evidence

    mean_R = retention_summary["mean_retention_rate"]
    L_bite = consequential_loss_summary["aggregate_consequential_loss_rate"]
    num_condensed_sessions = len(sessions_with_any_boundary)

    if num_condensed_sessions < 10 and len(compact_boundary_events) < 10:
        # Note: exactly 10 sessions have any boundary (3 compact + 7 away-only)
        # Check rule strictly:
        verdict = "insufficient_evidence"
        verdict_reason = (
            f"Only {num_condensed_sessions} sessions contain condensation/away boundaries "
            f"({len(compact_boundary_events)} compact_boundary, {len(away_summary_events)} away_summary). "
            "Pre-registered threshold requires >= 10 sessions for conclusive promotion."
        )
    elif mean_R >= 0.98:
        verdict = "falsifier_1_near_lossless"
        verdict_reason = f"Retention rate R = {mean_R:.1%} >= 98%. Condensation is near-lossless; retire perpetual memory."
    elif L_bite < 0.01:
        verdict = "falsifier_2_loss_does_not_bite"
        verdict_reason = f"Retention rate R = {mean_R:.1%} is lossy, but consequential loss L_bite = {L_bite:.2%} < 1.0%. Condensation discards safely; retire memory layer."
    else:
        verdict = "admitted_verifier_with_bite"
        verdict_reason = f"Retention rate R = {mean_R:.1%} < 98% and consequential loss L_bite = {L_bite:.2%} >= 1.0%. Condensation is an error-prone verifier with measurable operational bite."

    results = {
        "experiment_id": "EXP-45",
        "date": "2026-08-20",
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "longevity_and_frequency": longevity_summary,
        "retention_analysis": retention_summary,
        "consequential_loss_analysis": consequential_loss_summary,
        "survival_correlations": survival_correlations,
        "entity_sample_size": len(all_survival_rows),
    }

    if output_json_path:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as fp:
            json.dump(results, fp, indent=2)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="EXP-45: Condensation retention and loss analysis.")
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=Path("/mnt/c/Users/jpbpr/.claude/projects/"),
        help="Path to transcript directory",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/10-research/experiments/exp45/results-exp45.json"),
        help="Path to write output results JSON",
    )
    args = parser.parse_args()

    print(f"EXP-45 runner starting on corpus: {args.corpus_dir}")
    results = run_exp45_analysis(args.corpus_dir, args.output_json)

    print("\n--- EXP-45 Summary Results ---")
    print(f"Verdict: {results['verdict']}")
    print(f"Reason: {results['verdict_reason']}")
    print(f"Total Files: {results['longevity_and_frequency']['total_files']}, Sessions: {results['longevity_and_frequency']['total_unique_sessions']}")
    print(f"Boundaries: {results['longevity_and_frequency']['total_all_boundary_events']} ({results['longevity_and_frequency']['total_compact_boundary_events']} compact, {results['longevity_and_frequency']['total_away_summary_events']} away)")
    print(f"Session Lifespan Max: {results['longevity_and_frequency']['duration_days']['max']:.2f} days (p50: {results['longevity_and_frequency']['duration_days']['p50']:.4f} days)")
    print(f"Mean Retention Rate: {results['retention_analysis']['mean_retention_rate']:.1%} (95% CI: {results['retention_analysis']['retention_bootstrap_95ci']})")
    print(f"  Path Retention: {results['retention_analysis']['path_retention_mean']:.1%}, Ident Retention: {results['retention_analysis']['ident_retention_mean']:.1%}")
    print(f"Aggregate File Re-read Rate: {results['consequential_loss_analysis']['aggregate_file_reread_rate']:.1%} ({results['consequential_loss_analysis']['total_reread_files']}/{results['consequential_loss_analysis']['total_pre_read_files']})")
    print(f"Aggregate Consequential Loss Rate: {results['consequential_loss_analysis']['aggregate_consequential_loss_rate']:.2%}")
    print(f"Survival Correlations: {results['survival_correlations']}")
    print(f"Total Pre-Boundary Entity Instances Evaluated: {results['entity_sample_size']}")


if __name__ == "__main__":
    main()
