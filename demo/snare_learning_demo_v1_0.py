import argparse
import csv
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

VERSION = "1.0"

VISIBLE = "VISIBLE"
GROUPED = "GROUPED"
DELAYED = "DELAYED"
SILENT = "SILENT"
ASK_USER = "ASK_USER"
QUARANTINED = "QUARANTINED"

VALID_STATES = {VISIBLE, GROUPED, DELAYED, SILENT, ASK_USER, QUARANTINED}
RESOLUTION_ORDER = [VISIBLE, GROUPED, DELAYED, SILENT, ASK_USER, QUARANTINED]


def norm(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def truth(value):
    if isinstance(value, bool):
        return value
    return norm(value) in {"1", "true", "yes", "y"}


def hour_from_stamp(stamp):
    if not stamp:
        return 12
    text = str(stamp).strip()
    patterns = ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%H:%M"]
    for pattern in patterns:
        try:
            return datetime.strptime(text, pattern).hour
        except ValueError:
            pass
    return 12


def stable_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def certificate(obj, length=16):
    return hashlib.sha256(stable_json(obj).encode("utf-8")).hexdigest()[:length]


def state_from_user_decision(decision):
    text = norm(decision).replace(" ", "_").replace("-", "_")
    if text in {"visible", "show", "interrupt", "allow"}:
        return VISIBLE
    if text in {"grouped", "group", "digest"}:
        return GROUPED
    if text in {"delayed", "delay", "later"}:
        return DELAYED
    if text in {"silent", "mute", "quiet"}:
        return SILENT
    if text in {"quarantined", "quarantine", "risk", "hold"}:
        return QUARANTINED
    upper = str(decision).strip().upper()
    if upper in VALID_STATES:
        return upper
    return ASK_USER


@dataclass(frozen=True)
class Notification:
    id: str
    app: str
    sender: str
    category: str
    channel: str
    timestamp: str
    user_relation: str = "unknown"
    urgency: str = "normal"
    link_present: bool = False
    attachment_present: bool = False
    external_source: bool = False
    unknown_sender: bool = False
    promotional: bool = False
    system_critical: bool = False
    emergency: bool = False
    calendar_related: bool = False
    user_approved: bool = False
    work_related: bool = False


@dataclass(frozen=True)
class Resolution:
    id: str
    app: str
    sender: str
    category: str
    state: str
    interrupt: bool
    group_key: str
    delay_until: str
    policy_profile: str
    policy_action: str
    policy_reason: str
    reason: str
    risk_score: int
    priority_score: int
    budget_requested: bool
    budget_granted: bool
    budget_remaining_after: int
    visibility_gate: str
    emergency: bool
    emergency_safe: bool
    emergency_override: bool
    emergency_gate: str
    structure_complete: bool
    structure_consistent: bool
    rule_source: str
    rule_maturity: str
    rule_confidence: float
    rule_support: int
    rule_conflicts: int
    structure_signature: str
    trace_complete: bool
    trace_steps: str
    trace_certificate: str
    certificate: str




@dataclass(frozen=True)
class ProfileComparison:
    id: str
    app: str
    sender: str
    category: str
    default_state: str
    focus_mode_state: str
    work_mode_state: str
    family_mode_state: str
    sleep_mode_state: str
    default_interrupt: bool
    focus_mode_interrupt: bool
    work_mode_interrupt: bool
    family_mode_interrupt: bool
    sleep_mode_interrupt: bool
    state_variants: int
    interrupt_variants: int
    profile_difference: bool
    difference_summary: str
    comparison_certificate: str




@dataclass(frozen=True)
class AttentionLedgerRow:
    profile: str
    events_total: int
    visible_count: int
    grouped_count: int
    delayed_count: int
    silent_count: int
    ask_user_count: int
    quarantined_count: int
    interruptions_requested: int
    interruptions_granted: int
    interruptions_held: int
    emergency_events: int
    emergency_overrides: int
    emergency_blocked: int
    attention_spent: int
    budget_spent: int
    interruption_load_score: int
    ledger_certificate: str


@dataclass(frozen=True)
class MatureRule:
    structure_signature: str
    state: str
    group_key: str
    delay_until: str
    reason: str
    learned_from_ids: str
    support_count: int
    conflict_count: int
    confidence: float
    threshold: float
    maturity: str
    active: bool
    observed_states: str
    rule_certificate: str


def build_sample_notifications():
    return [
        Notification("N001", "Phone", "Mother", "call", "call", "2026-06-12 08:10", user_relation="family", urgency="high"),
        Notification("N002", "Calendar", "Calendar", "meeting", "push", "2026-06-12 09:00", calendar_related=True, user_approved=True),
        Notification("N003", "ShopApp", "MegaSale", "promotion", "push", "2026-06-12 10:15", promotional=True, link_present=True, external_source=True),
        Notification("N004", "NewsApp", "DailyNews", "news", "push", "2026-06-12 11:20"),
        Notification("N005", "NewsApp", "DailyNews", "news", "push", "2026-06-12 11:24"),
        Notification("N006", "Slack", "Work Team", "work", "push", "2026-06-12 22:30", work_related=True),
        Notification("N007", "Mail", "unknown@example.com", "email", "push", "2026-06-12 13:12", urgency="high", link_present=True, attachment_present=True, external_source=True, unknown_sender=True),
        Notification("N008", "Bank", "Bank Alert", "finance", "sms", "2026-06-12 14:05", user_approved=True, urgency="high"),
        Notification("N009", "UnknownApp", "Unknown", "unknown", "push", "2026-06-12 15:05", unknown_sender=True),
        Notification("N011", "UnknownApp", "Unknown", "unknown", "push", "2026-06-12 16:05", unknown_sender=True),
        Notification("N012", "ChatApp", "Unknown", "unknown_chat", "push", "2026-06-12 15:35", unknown_sender=True),
        Notification("N013", "ChatApp", "Unknown", "unknown_chat", "push", "2026-06-12 16:35", unknown_sender=True),
        Notification("N010", "System", "Device", "security", "push", "2026-06-12 16:45", system_critical=True, urgency="high"),
    ]


def build_sample_future_notifications():
    return [
        Notification("F001", "UnknownApp", "Unknown", "unknown", "push", "2026-06-13 15:05", unknown_sender=True),
        Notification("F002", "UnknownApp", "Unknown", "unknown", "push", "2026-06-14 16:45", unknown_sender=True),
        Notification("F003", "NewsApp", "DailyNews", "news", "push", "2026-06-13 11:20"),
        Notification("F004", "Mail", "unknown@example.com", "email", "push", "2026-06-13 13:12", urgency="high", link_present=True, attachment_present=True, external_source=True, unknown_sender=True),
        Notification("F005", "Slack", "Work Team", "work", "push", "2026-06-13 22:30", work_related=True),
        Notification("F006", "ChatApp", "Unknown", "unknown_chat", "push", "2026-06-13 15:35", unknown_sender=True),
        Notification("F007", "Phone", "Father", "call", "call", "2026-06-13 18:10", user_relation="family", urgency="high"),
        Notification("F008", "Bank", "Bank Alert", "finance", "sms", "2026-06-13 18:15", user_approved=True, urgency="high"),
        Notification("F009", "System", "Device", "security", "push", "2026-06-13 18:20", system_critical=True, urgency="high"),
        Notification("F010", "HealthMonitor", "Emergency Sensor", "medical", "push", "2026-06-13 18:25", user_approved=True, urgency="critical", emergency=True),
        Notification("F011", "UnknownAlert", "Unknown", "security", "push", "2026-06-13 18:30", urgency="critical", emergency=True, unknown_sender=True, link_present=True, external_source=True),
    ]


def build_sample_decisions():
    return {"N009": "SILENT", "N011": "SILENT", "N012": "VISIBLE", "N013": "SILENT"}


def row_to_notification(row):
    return Notification(
        id=str(row.get("id", "")).strip(),
        app=str(row.get("app", "")).strip(),
        sender=str(row.get("sender", "")).strip(),
        category=str(row.get("category", "")).strip(),
        channel=str(row.get("channel", "push")).strip(),
        timestamp=str(row.get("timestamp", "")).strip(),
        user_relation=str(row.get("user_relation", "unknown")).strip(),
        urgency=str(row.get("urgency", "normal")).strip(),
        link_present=truth(row.get("link_present", False)),
        attachment_present=truth(row.get("attachment_present", False)),
        external_source=truth(row.get("external_source", False)),
        unknown_sender=truth(row.get("unknown_sender", False)),
        promotional=truth(row.get("promotional", False)),
        system_critical=truth(row.get("system_critical", False)),
        emergency=truth(row.get("emergency", False)),
        calendar_related=truth(row.get("calendar_related", False)),
        user_approved=truth(row.get("user_approved", False)),
        work_related=truth(row.get("work_related", False)),
    )


def load_notifications(path, future=False):
    if not path:
        return build_sample_future_notifications() if future else build_sample_notifications()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        return [row_to_notification(item) for item in data]
    with p.open("r", encoding="utf-8", newline="") as f:
        return [row_to_notification(row) for row in csv.DictReader(f)]


def load_decisions(path):
    if not path:
        return build_sample_decisions()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): state_from_user_decision(v) for k, v in data.items()}
        return {str(item.get("id", "")): state_from_user_decision(item.get("decision", item.get("state", ""))) for item in data}
    decisions = {}
    with p.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            decisions[str(row.get("id", "")).strip()] = state_from_user_decision(row.get("decision", row.get("state", "")))
    return decisions


def is_complete(n):
    required = [n.id, n.app, n.sender, n.category, n.channel, n.timestamp]
    return all(str(x).strip() for x in required)


def is_consistent(n):
    if n.system_critical and n.promotional:
        return False
    if norm(n.user_relation) == "family" and n.unknown_sender:
        return False
    return True


def risk_score(n):
    score = 0
    if n.unknown_sender:
        score += 3
    if n.link_present:
        score += 2
    if n.attachment_present:
        score += 2
    if n.external_source:
        score += 1
    if norm(n.urgency) in {"high", "urgent", "critical"} and n.unknown_sender:
        score += 2
    return score


def time_band(n):
    hour = hour_from_stamp(n.timestamp)
    if hour < 8:
        return "night"
    if hour < 12:
        return "morning"
    if hour < 17:
        return "day"
    if hour < 19:
        return "evening"
    return "after_hours"


def structure_signature(n):
    payload = {
        "app": norm(n.app),
        "category": norm(n.category),
        "channel": norm(n.channel),
        "user_relation": norm(n.user_relation),
        "urgency": norm(n.urgency),
        "time_band": time_band(n),
        "link_present": bool(n.link_present),
        "attachment_present": bool(n.attachment_present),
        "external_source": bool(n.external_source),
        "unknown_sender": bool(n.unknown_sender),
        "promotional": bool(n.promotional),
        "system_critical": bool(n.system_critical),
        "emergency": bool(n.emergency),
        "calendar_related": bool(n.calendar_related),
        "user_approved": bool(n.user_approved),
        "work_related": bool(n.work_related),
    }
    return certificate(payload, 24)


def resolve_by_base_structure(n):
    complete = is_complete(n)
    consistent = is_consistent(n)
    risk = risk_score(n)
    hour = hour_from_stamp(n.timestamp)
    group_key = ""
    delay_until = ""

    if not complete:
        state = ASK_USER
        reason = "INCOMPLETE_STRUCTURE"
    elif not consistent:
        state = QUARANTINED
        reason = "CONFLICTING_STRUCTURE"
    elif risk >= 5:
        state = QUARANTINED
        reason = "RISK_STRUCTURE_LINK_ATTACHMENT_UNKNOWN"
    elif n.emergency and risk <= 2:
        state = VISIBLE
        reason = "EMERGENCY_STRUCTURE_ADMISSIBLE"
    elif n.emergency and risk > 2:
        state = QUARANTINED
        reason = "EMERGENCY_RISK_EXCEEDS_SAFE_LIMIT"
    elif n.system_critical:
        state = VISIBLE
        reason = "SYSTEM_CRITICAL_ADMISSIBLE"
    elif norm(n.user_relation) == "family":
        state = VISIBLE
        reason = "FAMILY_RELATION_ADMISSIBLE"
    elif n.calendar_related or n.user_approved:
        state = VISIBLE
        reason = "USER_APPROVED_OR_CALENDAR_ADMISSIBLE"
    elif n.promotional or norm(n.category) in {"promotion", "ads", "marketing"}:
        state = SILENT
        reason = "PROMOTION_NOT_INTERRUPT_ADMISSIBLE"
    elif norm(n.category) in {"news", "social", "updates"}:
        state = GROUPED
        reason = "GROUP_VISIBILITY_ADMISSIBLE"
        group_key = norm(n.category) or "general"
    elif n.work_related and (hour < 8 or hour >= 19):
        state = DELAYED
        reason = "WORK_AFTER_HOURS_DELAYED"
        delay_until = "next_work_window_09:00"
    elif n.unknown_sender:
        state = ASK_USER
        reason = "UNKNOWN_STRUCTURE_REQUIRES_USER_DECISION"
    else:
        state = GROUPED
        reason = "DEFAULT_GROUPED_VISIBILITY"
        group_key = norm(n.category) or "general"

    return state, group_key, delay_until, reason, risk, complete, consistent



def canonical_policy(profile):
    text = norm(profile).replace("-", "_").replace(" ", "_").upper()
    allowed = {"DEFAULT", "FOCUS_MODE", "WORK_MODE", "FAMILY_MODE", "SLEEP_MODE"}
    if text in allowed:
        return text
    return "DEFAULT"

def apply_policy_profile(n, state, group_key, delay_until, reason, profile):
    profile = canonical_policy(profile)
    action = "POLICY_NO_CHANGE"
    policy_reason = profile + "_NO_CHANGE"
    if profile == "DEFAULT":
        return state, group_key, delay_until, reason, action, policy_reason
    if state in {QUARANTINED, ASK_USER}:
        return state, group_key, delay_until, reason, action, policy_reason
    if n.emergency or n.system_critical:
        return state, group_key, delay_until, reason, action, policy_reason
    if profile == "FOCUS_MODE":
        if norm(n.user_relation) == "family" or norm(n.category) in {"finance", "bank", "security"}:
            return state, group_key, delay_until, reason, "POLICY_PRESERVE_VISIBLE", "FOCUS_MODE_CRITICAL_OR_FAMILY_ALLOWED"
        if state == VISIBLE:
            return DELAYED, "", "next_focus_break", reason + "_FOCUS_DELAYED", "POLICY_DELAY", "FOCUS_MODE_VISIBLE_DELAYED"
        if state == GROUPED:
            return SILENT, "", "", reason + "_FOCUS_SILENT", "POLICY_SILENCE", "FOCUS_MODE_GROUPED_SILENCED"
        return state, group_key, delay_until, reason, action, policy_reason
    if profile == "WORK_MODE":
        if n.work_related and state in {GROUPED, DELAYED, SILENT}:
            return VISIBLE, "", "", reason + "_WORK_VISIBLE", "POLICY_PROMOTE", "WORK_MODE_WORK_VISIBLE"
        if norm(n.user_relation) == "family":
            return state, group_key, delay_until, reason, "POLICY_PRESERVE_VISIBLE", "WORK_MODE_FAMILY_ALLOWED"
        if norm(n.category) in {"news", "social", "updates"}:
            return GROUPED, norm(n.category) or "general", "", reason + "_WORK_GROUPED", "POLICY_GROUP", "WORK_MODE_NON_WORK_GROUPED"
        return state, group_key, delay_until, reason, action, policy_reason
    if profile == "FAMILY_MODE":
        if norm(n.user_relation) == "family":
            return VISIBLE, "", "", reason + "_FAMILY_VISIBLE", "POLICY_PROMOTE", "FAMILY_MODE_FAMILY_VISIBLE"
        if n.work_related and state == VISIBLE:
            return DELAYED, "", "next_work_window", reason + "_FAMILY_DELAYED", "POLICY_DELAY", "FAMILY_MODE_WORK_DELAYED"
        return state, group_key, delay_until, reason, action, policy_reason
    if profile == "SLEEP_MODE":
        if n.emergency or n.system_critical:
            return state, group_key, delay_until, reason, "POLICY_PRESERVE_VISIBLE", "SLEEP_MODE_CRITICAL_ALLOWED"
        if norm(n.user_relation) == "family" and norm(n.urgency) in {"high", "urgent", "critical"}:
            return state, group_key, delay_until, reason, "POLICY_PRESERVE_VISIBLE", "SLEEP_MODE_URGENT_FAMILY_ALLOWED"
        if state == VISIBLE:
            return DELAYED, "", "morning_visibility_window", reason + "_SLEEP_DELAYED", "POLICY_DELAY", "SLEEP_MODE_VISIBLE_DELAYED"
        if state == GROUPED:
            return SILENT, "", "", reason + "_SLEEP_SILENT", "POLICY_SILENCE", "SLEEP_MODE_GROUPED_SILENCED"
        return state, group_key, delay_until, reason, action, policy_reason
    return state, group_key, delay_until, reason, action, policy_reason

def priority_score(n, state, risk):
    score = 0
    if state == VISIBLE:
        score += 50
    if n.emergency:
        score += 50
    if n.system_critical:
        score += 45
    if norm(n.user_relation) == "family":
        score += 35
    if norm(n.category) in {"finance", "bank", "security"}:
        score += 25
    if n.calendar_related:
        score += 20
    if n.user_approved:
        score += 15
    if norm(n.urgency) in {"high", "urgent", "critical"}:
        score += 10
    if risk >= 5:
        score -= 40
    if state in {SILENT, GROUPED, DELAYED, ASK_USER, QUARANTINED}:
        score -= 25
    if score < 0:
        score = 0
    if score > 100:
        score = 100
    return score


def trace_join(steps):
    return " -> ".join(steps)


def trace_certificate_for(steps):
    return certificate({"version": VERSION, "trace_steps": steps}, 16)


def base_trace(n, state, risk, complete, consistent, reason):
    steps = []
    steps.append("EVENT_RECEIVED")
    steps.append("STRUCTURE_COMPLETE=" + str(complete))
    steps.append("STRUCTURE_CONSISTENT=" + str(consistent))
    steps.append("RISK_SCORE=" + str(risk))
    steps.append("BASE_STATE=" + state)
    steps.append("BASE_REASON=" + reason)
    return steps


def trace_is_complete(steps):
    required = ["EVENT_RECEIVED", "STRUCTURE_COMPLETE", "STRUCTURE_CONSISTENT", "RISK_SCORE", "BASE_STATE", "FINAL_STATE", "INTERRUPT"]
    text = trace_join(steps)
    return all(item in text for item in required)

def resolve_notification(n, rules=None, policy_profile="DEFAULT"):
    rules = rules or {}
    sig = structure_signature(n)
    base_state, group_key, delay_until, reason, risk, complete, consistent = resolve_by_base_structure(n)
    trace_steps = base_trace(n, base_state, risk, complete, consistent, reason)
    rule_source = "BASE_STRUCTURE"
    rule_maturity = "NONE"
    rule_confidence = 0.0
    rule_support = 0
    rule_conflicts = 0
    state = base_state

    if base_state == ASK_USER and sig in rules:
        rule = rules[sig]
        rule_maturity = rule.maturity
        rule_confidence = rule.confidence
        rule_support = rule.support_count
        rule_conflicts = rule.conflict_count
        trace_steps.append("RULE_FOUND=" + rule.maturity)
        trace_steps.append("RULE_CONFIDENCE=" + str(rule.confidence))
        trace_steps.append("RULE_SUPPORT=" + str(rule.support_count))
        trace_steps.append("RULE_CONFLICTS=" + str(rule.conflict_count))
        if rule.active:
            state = rule.state
            group_key = rule.group_key
            delay_until = rule.delay_until
            reason = "MATURE_RULE_APPLIED_FROM_" + rule.learned_from_ids
            rule_source = "MATURE_RULE"
            trace_steps.append("RULE_DECISION=APPLIED")
        elif rule.maturity == "CONFLICTED":
            reason = "RULE_CONFLICT_REQUIRES_USER_DECISION"
            rule_source = "CONFLICTED_RULE"
            trace_steps.append("RULE_DECISION=BLOCKED_CONFLICT")
        else:
            reason = "RULE_NOT_MATURE_REQUIRES_USER_DECISION"
            rule_source = "IMMATURE_RULE"
            trace_steps.append("RULE_DECISION=BLOCKED_IMMATURE")
    else:
        trace_steps.append("RULE_FOUND=NO")
        trace_steps.append("RULE_DECISION=BASE_STRUCTURE")

    policy_profile = canonical_policy(policy_profile)
    before_policy_state = state
    state, group_key, delay_until, reason, policy_action, policy_reason = apply_policy_profile(n, state, group_key, delay_until, reason, policy_profile)
    trace_steps.append("POLICY_PROFILE=" + policy_profile)
    trace_steps.append("POLICY_ACTION=" + policy_action)
    trace_steps.append("POLICY_REASON=" + policy_reason)
    trace_steps.append("POLICY_STATE_BEFORE=" + before_policy_state)
    trace_steps.append("POLICY_STATE_AFTER=" + state)
    priority = priority_score(n, state, risk)
    budget_requested = state == VISIBLE
    budget_granted = False
    budget_remaining_after = -1
    visibility_gate = "PENDING_ATTENTION_BUDGET" if budget_requested else "NO_INTERRUPTION_REQUESTED"
    emergency = bool(n.emergency)
    emergency_safe = emergency and risk <= 2 and complete and consistent and state == VISIBLE
    emergency_override = False
    emergency_gate = "EMERGENCY_SAFE_PENDING_BUDGET" if emergency_safe else ("EMERGENCY_RISK_BLOCKED" if emergency else "NO_EMERGENCY")
    interrupt = False
    trace_steps.append("FINAL_STATE=" + state)
    trace_steps.append("PRIORITY_SCORE=" + str(priority))
    trace_steps.append("BUDGET_REQUESTED=" + str(budget_requested))
    trace_steps.append("EMERGENCY=" + str(emergency))
    trace_steps.append("EMERGENCY_SAFE=" + str(emergency_safe))
    trace_steps.append("VISIBILITY_GATE=" + visibility_gate)
    trace_steps.append("INTERRUPT=" + str(interrupt))
    trace_complete = trace_is_complete(trace_steps)
    trace_text = trace_join(trace_steps)
    trace_cert = trace_certificate_for(trace_steps)
    payload = {
        "version": VERSION,
        "notification": asdict(n),
        "state": state,
        "interrupt": interrupt,
        "group_key": group_key,
        "delay_until": delay_until,
        "policy_profile": policy_profile,
        "policy_action": policy_action,
        "policy_reason": policy_reason,
        "reason": reason,
        "risk_score": risk,
        "priority_score": priority,
        "budget_requested": budget_requested,
        "budget_granted": budget_granted,
        "budget_remaining_after": budget_remaining_after,
        "visibility_gate": visibility_gate,
        "emergency": emergency,
        "emergency_safe": emergency_safe,
        "emergency_override": emergency_override,
        "emergency_gate": emergency_gate,
        "structure_complete": complete,
        "structure_consistent": consistent,
        "rule_source": rule_source,
        "rule_maturity": rule_maturity,
        "rule_confidence": rule_confidence,
        "rule_support": rule_support,
        "rule_conflicts": rule_conflicts,
        "structure_signature": sig,
        "trace_complete": trace_complete,
        "trace_steps": trace_text,
        "trace_certificate": trace_cert,
    }
    return Resolution(n.id, n.app, n.sender, n.category, state, interrupt, group_key, delay_until, policy_profile, policy_action, policy_reason, reason, risk, priority, budget_requested, budget_granted, budget_remaining_after, visibility_gate, emergency, emergency_safe, emergency_override, emergency_gate, complete, consistent, rule_source, rule_maturity, rule_confidence, rule_support, rule_conflicts, sig, trace_complete, trace_text, trace_cert, certificate(payload))


def choose_state(state_counts):
    best_state = ASK_USER
    best_count = -1
    for state in RESOLUTION_ORDER:
        count = state_counts.get(state, 0)
        if count > best_count:
            best_state = state
            best_count = count
    return best_state, best_count


def confidence_from_counts(support_count, conflict_count):
    value = 0.50 + support_count * 0.15 - conflict_count * 0.25
    if value < 0.0:
        value = 0.0
    if value > 0.99:
        value = 0.99
    return round(value, 2)


def learn_rules(notifications, initial_results, decisions, threshold):
    by_id = {n.id: n for n in notifications}
    by_result = {r.id: r for r in initial_results}
    evidence = {}

    for item_id, decision in decisions.items():
        if item_id not in by_id:
            continue
        state = state_from_user_decision(decision)
        if state == ASK_USER:
            continue
        result = by_result.get(item_id)
        if result is None or result.state != ASK_USER:
            continue
        sig = structure_signature(by_id[item_id])
        if sig not in evidence:
            evidence[sig] = []
        evidence[sig].append((item_id, state))

    rules = {}
    for sig, items in evidence.items():
        state_counts = {}
        ids = []
        for item_id, state in items:
            ids.append(item_id)
            state_counts[state] = state_counts.get(state, 0) + 1
        selected_state, support_count = choose_state(state_counts)
        conflict_count = len(items) - support_count
        confidence = confidence_from_counts(support_count, conflict_count)
        if conflict_count > 0:
            maturity = "CONFLICTED"
        elif confidence >= threshold:
            maturity = "ACTIVE"
        else:
            maturity = "PENDING"
        active = maturity == "ACTIVE"
        group_key = "general" if selected_state == GROUPED else ""
        delay_until = "next_visibility_window" if selected_state == DELAYED else ""
        observed_states = ";".join([state + ":" + str(state_counts[state]) for state in sorted(state_counts)])
        reason = "USER_DECISION_RULE_" + maturity
        learned_from_ids = "+".join(ids)
        payload = {
            "version": VERSION,
            "structure_signature": sig,
            "state": selected_state,
            "group_key": group_key,
            "delay_until": delay_until,
            "reason": reason,
            "learned_from_ids": learned_from_ids,
            "support_count": support_count,
            "conflict_count": conflict_count,
            "confidence": confidence,
            "threshold": threshold,
            "maturity": maturity,
            "active": active,
            "observed_states": observed_states,
        }
        rules[sig] = MatureRule(sig, selected_state, group_key, delay_until, reason, learned_from_ids, support_count, conflict_count, confidence, threshold, maturity, active, observed_states, certificate(payload))
    return rules



def apply_attention_budget(results, budget, priority_threshold):
    remaining = budget
    ranked = sorted(results, key=lambda r: (-r.priority_score, r.id))
    granted_ids = set()
    for r in ranked:
        if r.emergency_safe:
            continue
        if r.state == VISIBLE and r.priority_score >= priority_threshold and remaining > 0:
            granted_ids.add(r.id)
            remaining -= 1
    output = []
    current_remaining = budget
    for r in results:
        requested = r.state == VISIBLE
        emergency_override = False
        emergency_gate = r.emergency_gate
        if r.emergency_safe:
            granted = False
            gate = "EMERGENCY_OVERRIDE_GRANTED"
            after = current_remaining
            interrupt = True
            emergency_override = True
            emergency_gate = "EMERGENCY_SAFE_OVERRIDE"
            reason = r.reason + "_EMERGENCY_OVERRIDE"
        else:
            granted = r.id in granted_ids
            if not requested:
                gate = "NO_INTERRUPTION_REQUESTED"
                after = current_remaining
                interrupt = False
                reason = r.reason
            elif granted:
                current_remaining -= 1
                gate = "INTERRUPTION_BUDGET_GRANTED"
                after = current_remaining
                interrupt = True
                reason = r.reason
            elif r.priority_score < priority_threshold:
                gate = "PRIORITY_BELOW_THRESHOLD"
                after = current_remaining
                interrupt = False
                reason = r.reason + "_PRIORITY_HELD"
            else:
                gate = "INTERRUPTION_BUDGET_EXHAUSTED"
                after = current_remaining
                interrupt = False
                reason = r.reason + "_BUDGET_HELD"
        trace_steps = r.trace_steps.split(" -> ") if r.trace_steps else []
        if trace_steps and trace_steps[-1].startswith("INTERRUPT="):
            trace_steps = trace_steps[:-1]
        if trace_steps and trace_steps[-1].startswith("VISIBILITY_GATE="):
            trace_steps = trace_steps[:-1]
        trace_steps.append("ATTENTION_BUDGET=" + str(budget))
        trace_steps.append("BUDGET_GRANTED=" + str(granted))
        trace_steps.append("BUDGET_REMAINING_AFTER=" + str(after))
        trace_steps.append("EMERGENCY_OVERRIDE=" + str(emergency_override))
        trace_steps.append("VISIBILITY_GATE=" + gate)
        trace_steps.append("INTERRUPT=" + str(interrupt))
        trace_complete = trace_is_complete(trace_steps)
        trace_text = trace_join(trace_steps)
        trace_cert = trace_certificate_for(trace_steps)
        payload = asdict(r)
        payload.update({
            "version": VERSION,
            "interrupt": interrupt,
            "budget_requested": requested,
            "budget_granted": granted,
            "budget_remaining_after": after,
            "visibility_gate": gate,
            "emergency_override": emergency_override,
            "emergency_gate": emergency_gate,
            "reason": reason,
            "trace_complete": trace_complete,
            "trace_steps": trace_text,
            "trace_certificate": trace_cert,
        })
        output.append(Resolution(r.id, r.app, r.sender, r.category, r.state, interrupt, r.group_key, r.delay_until, r.policy_profile, r.policy_action, r.policy_reason, reason, r.risk_score, r.priority_score, requested, granted, after, gate, r.emergency, r.emergency_safe, emergency_override, emergency_gate, r.structure_complete, r.structure_consistent, r.rule_source, r.rule_maturity, r.rule_confidence, r.rule_support, r.rule_conflicts, r.structure_signature, trace_complete, trace_text, trace_cert, certificate(payload)))
    return output


def count_budget(results):
    data = {"requested": 0, "granted": 0, "held": 0}
    for r in results:
        if r.budget_requested:
            data["requested"] += 1
        if r.budget_granted:
            data["granted"] += 1
        if r.budget_requested and not r.budget_granted:
            data["held"] += 1
    return data

def count_emergency(results):
    data = {"emergency_events": 0, "overrides": 0, "blocked": 0}
    for r in results:
        if r.emergency:
            data["emergency_events"] += 1
        if r.emergency_override:
            data["overrides"] += 1
        if r.emergency and not r.emergency_safe:
            data["blocked"] += 1
    return data


def count_policy_actions(results):
    data = {}
    for r in results:
        data[r.policy_action] = data.get(r.policy_action, 0) + 1
    return data

def grouped_summary(results):
    groups = {}
    for r in results:
        if r.state == GROUPED:
            key = r.group_key or norm(r.category) or "general"
            groups[key] = groups.get(key, 0) + 1
    return groups


def count_states(results):
    counts = {}
    for r in results:
        counts[r.state] = counts.get(r.state, 0) + 1
    return counts


def count_rule_maturity(rules):
    counts = {}
    for rule in rules.values():
        counts[rule.maturity] = counts.get(rule.maturity, 0) + 1
    return counts


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(asdict(rows[0]).keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))



PROFILE_ORDER = ["DEFAULT", "FOCUS_MODE", "WORK_MODE", "FAMILY_MODE", "SLEEP_MODE"]


def resolve_profile_set(notifications, rules, interruption_budget, priority_threshold):
    resolved = {}
    for profile in PROFILE_ORDER:
        base_results = [resolve_notification(n, rules, policy_profile=profile) for n in notifications]
        resolved[profile] = apply_attention_budget(base_results, interruption_budget, priority_threshold)
    return resolved


def compare_profile_results(profile_results):
    comparisons = []
    if not profile_results:
        return comparisons
    ids = [r.id for r in profile_results[PROFILE_ORDER[0]]]
    for item_id in ids:
        by_profile = {}
        for profile in PROFILE_ORDER:
            match = [r for r in profile_results[profile] if r.id == item_id]
            if match:
                by_profile[profile] = match[0]
        if len(by_profile) != len(PROFILE_ORDER):
            continue
        states = {profile: by_profile[profile].state for profile in PROFILE_ORDER}
        interrupts = {profile: by_profile[profile].interrupt for profile in PROFILE_ORDER}
        state_variants = len(set(states.values()))
        interrupt_variants = len(set(interrupts.values()))
        profile_difference = state_variants > 1 or interrupt_variants > 1
        first = by_profile[PROFILE_ORDER[0]]
        difference_summary = ";".join([profile + "=" + states[profile] + "/" + str(interrupts[profile]) for profile in PROFILE_ORDER])
        payload = {
            "version": VERSION,
            "id": item_id,
            "states": states,
            "interrupts": interrupts,
            "state_variants": state_variants,
            "interrupt_variants": interrupt_variants,
            "profile_difference": profile_difference,
        }
        comparisons.append(ProfileComparison(
            item_id,
            first.app,
            first.sender,
            first.category,
            states["DEFAULT"],
            states["FOCUS_MODE"],
            states["WORK_MODE"],
            states["FAMILY_MODE"],
            states["SLEEP_MODE"],
            interrupts["DEFAULT"],
            interrupts["FOCUS_MODE"],
            interrupts["WORK_MODE"],
            interrupts["FAMILY_MODE"],
            interrupts["SLEEP_MODE"],
            state_variants,
            interrupt_variants,
            profile_difference,
            difference_summary,
            certificate(payload),
        ))
    return comparisons


def count_profile_differences(comparisons):
    data = {"events_compared": len(comparisons), "different": 0, "same": 0}
    for row in comparisons:
        if row.profile_difference:
            data["different"] += 1
        else:
            data["same"] += 1
    return data




def build_attention_ledger(profile_results):
    rows = []
    for profile in PROFILE_ORDER:
        results = profile_results.get(profile, [])
        counts = count_states(results)
        budget = count_budget(results)
        emergency = count_emergency(results)
        attention_spent = sum(1 for r in results if r.interrupt)
        budget_spent = sum(1 for r in results if r.budget_granted)
        interruption_load_score = attention_spent * 100 + budget["held"] * 25 + emergency["blocked"] * 10
        payload = {
            "version": VERSION,
            "profile": profile,
            "events_total": len(results),
            "attention_spent": attention_spent,
            "budget_spent": budget_spent,
            "interruption_load_score": interruption_load_score,
        }
        rows.append(AttentionLedgerRow(
            profile,
            len(results),
            counts.get(VISIBLE, 0),
            counts.get(GROUPED, 0),
            counts.get(DELAYED, 0),
            counts.get(SILENT, 0),
            counts.get(ASK_USER, 0),
            counts.get(QUARANTINED, 0),
            budget["requested"],
            budget["granted"],
            budget["held"],
            emergency["emergency_events"],
            emergency["overrides"],
            emergency["blocked"],
            attention_spent,
            budget_spent,
            interruption_load_score,
            certificate(payload),
        ))
    return rows

def summarize_attention_ledger(ledger_rows):
    if not ledger_rows:
        return {"profiles": 0, "total_attention_spent": 0, "lowest_load_profile": "", "highest_load_profile": ""}
    lowest = min(ledger_rows, key=lambda r: (r.interruption_load_score, r.attention_spent, r.profile))
    highest = max(ledger_rows, key=lambda r: (r.interruption_load_score, r.attention_spent, r.profile))
    return {
        "profiles": len(ledger_rows),
        "total_attention_spent": sum(r.attention_spent for r in ledger_rows),
        "lowest_load_profile": lowest.profile,
        "highest_load_profile": highest.profile,
    }

def write_outputs(initial_results, future_results, rules, comparison_rows, ledger_rows, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    initial_csv = out / "snare_initial_resolution_report_v1_0.csv"
    initial_json = out / "snare_initial_resolution_report_v1_0.json"
    future_csv = out / "snare_future_resolution_report_v1_0.csv"
    future_json = out / "snare_future_resolution_report_v1_0.json"
    rules_csv = out / "snare_mature_rules_v1_0.csv"
    rules_json = out / "snare_mature_rules_v1_0.json"
    comparison_csv = out / "snare_profile_comparison_report_v1_0.csv"
    comparison_json = out / "snare_profile_comparison_report_v1_0.json"
    ledger_csv = out / "snare_attention_ledger_v1_0.csv"
    ledger_json = out / "snare_attention_ledger_v1_0.json"
    write_csv(initial_csv, initial_results)
    write_csv(future_csv, future_results)
    rule_rows = list(rules.values())
    write_csv(rules_csv, rule_rows)
    write_csv(comparison_csv, comparison_rows)
    write_csv(ledger_csv, ledger_rows)
    initial_json.write_text(json.dumps([asdict(r) for r in initial_results], indent=2), encoding="utf-8")
    future_json.write_text(json.dumps([asdict(r) for r in future_results], indent=2), encoding="utf-8")
    rules_json.write_text(json.dumps([asdict(r) for r in rule_rows], indent=2), encoding="utf-8")
    comparison_json.write_text(json.dumps([asdict(r) for r in comparison_rows], indent=2), encoding="utf-8")
    ledger_json.write_text(json.dumps([asdict(r) for r in ledger_rows], indent=2), encoding="utf-8")
    return initial_csv, initial_json, rules_csv, rules_json, future_csv, future_json, comparison_csv, comparison_json, ledger_csv, ledger_json


def print_counts(title, results):
    counts = count_states(results)
    print(title)
    for state in RESOLUTION_ORDER:
        print(state.ljust(14) + ": " + str(counts.get(state, 0)))
    print()


def print_report(initial_results, rules, future_results, comparison_rows, ledger_rows, threshold, priority_threshold, interruption_budget, policy_profile):
    print("SNARE v" + VERSION)
    print("Structural Notification Resolution Engine")
    print("========================================================================")
    print("Principle: notification_visible iff structure_admissible")
    print("Language: event_exists != event_visible")
    print("Learning law: first_unknown -> ask_user -> rule_signature -> future_resolution")
    print("Maturity law: rule_active iff confidence >= threshold AND conflicts = 0")
    print("Attention law: interrupt_allowed iff state = VISIBLE AND priority >= threshold AND budget_available")
    print("Emergency law: emergency_interrupt_allowed iff emergency = true AND risk <= safe_limit")
    print("Explanation law: decision_trustworthy iff reason_chain is complete")
    print("Policy law: visibility_resolution = resolve(event_structure, active_policy_profile)")
    print("Comparison law: profile_difference = resolve(event, profile_a) != resolve(event, profile_b)")
    print("Attention ledger law: attention_spent = sum(interruptions_granted)")
    print("Release law: release_ready iff resolution + learning + maturity + budget + emergency + trace + profile + comparison + ledger pass")
    print("Active policy profile: " + canonical_policy(policy_profile))
    print("Rule confidence threshold: " + str(threshold))
    print("Priority threshold: " + str(priority_threshold))
    print("Interruption budget: " + str(interruption_budget))
    print("Emergency safe limit: 2")
    print()
    print_counts("Initial Resolution Summary", initial_results)
    maturity_counts = count_rule_maturity(rules)
    print("Rule Maturity Summary")
    print("rules_total  : " + str(len(rules)))
    print("ACTIVE       : " + str(maturity_counts.get("ACTIVE", 0)))
    print("PENDING      : " + str(maturity_counts.get("PENDING", 0)))
    print("CONFLICTED   : " + str(maturity_counts.get("CONFLICTED", 0)))
    for rule in rules.values():
        text = [
            "signature=" + rule.structure_signature,
            "state=" + rule.state,
            "maturity=" + rule.maturity,
            "confidence=" + str(rule.confidence),
            "support=" + str(rule.support_count),
            "conflicts=" + str(rule.conflict_count),
            "from=" + rule.learned_from_ids,
            "certificate=" + rule.rule_certificate,
        ]
        print(" | ".join(text))
    print()
    print_counts("Future Resolution Summary", future_results)
    budget_counts = count_budget(future_results)
    print("Attention Budget Summary")
    print("requested    : " + str(budget_counts["requested"]))
    print("granted      : " + str(budget_counts["granted"]))
    print("held         : " + str(budget_counts["held"]))
    print()
    emergency_counts = count_emergency(future_results)
    print("Emergency Override Summary")
    print("emergency_events : " + str(emergency_counts["emergency_events"]))
    print("overrides        : " + str(emergency_counts["overrides"]))
    print("blocked          : " + str(emergency_counts["blocked"]))
    print()
    policy_counts = count_policy_actions(future_results)
    print("Policy Profile Summary")
    print("profile      : " + canonical_policy(policy_profile))
    for key in sorted(policy_counts):
        print(key.ljust(18) + ": " + str(policy_counts[key]))
    print()
    comparison_counts = count_profile_differences(comparison_rows)
    print("Multi-Profile Comparison Summary")
    print("events_compared : " + str(comparison_counts["events_compared"]))
    print("different       : " + str(comparison_counts["different"]))
    print("same            : " + str(comparison_counts["same"]))
    print()
    groups = grouped_summary(future_results)
    if groups:
        print("Grouped Visibility")
        for key, count in sorted(groups.items()):
            print(str(count).rjust(3) + " notifications available in group: " + key)
        print()
    print("Profile Differences")
    for row in comparison_rows:
        if row.profile_difference:
            print(row.id + " | variants=" + str(row.state_variants) + " | interrupts=" + str(row.interrupt_variants) + " | " + row.difference_summary + " | certificate=" + row.comparison_certificate)
    print()
    ledger_summary = summarize_attention_ledger(ledger_rows)
    print("Personal Attention Ledger Summary")
    print("profiles               : " + str(ledger_summary["profiles"]))
    print("total_attention_spent  : " + str(ledger_summary["total_attention_spent"]))
    print("lowest_load_profile    : " + ledger_summary["lowest_load_profile"])
    print("highest_load_profile   : " + ledger_summary["highest_load_profile"])
    for row in ledger_rows:
        print(row.profile + " | attention_spent=" + str(row.attention_spent) + " | budget_spent=" + str(row.budget_spent) + " | requested=" + str(row.interruptions_requested) + " | held=" + str(row.interruptions_held) + " | emergency_overrides=" + str(row.emergency_overrides) + " | load_score=" + str(row.interruption_load_score) + " | certificate=" + row.ledger_certificate)
    print()
    print("Detailed Future Resolution")
    for r in future_results:
        text = [
            r.id,
            r.state,
            "interrupt=" + str(r.interrupt),
            "profile=" + r.policy_profile,
            "policy_action=" + r.policy_action,
            "rule_source=" + r.rule_source,
            "maturity=" + r.rule_maturity,
            "confidence=" + str(r.rule_confidence),
            "support=" + str(r.rule_support),
            "conflicts=" + str(r.rule_conflicts),
            "risk=" + str(r.risk_score),
            "priority=" + str(r.priority_score),
            "budget_granted=" + str(r.budget_granted),
            "gate=" + r.visibility_gate,
            "emergency=" + str(r.emergency),
            "emergency_safe=" + str(r.emergency_safe),
            "emergency_override=" + str(r.emergency_override),
            "emergency_gate=" + r.emergency_gate,
            "reason=" + r.reason,
            "signature=" + r.structure_signature,
            "trace_complete=" + str(r.trace_complete),
            "trace_certificate=" + r.trace_certificate,
            "certificate=" + r.certificate,
        ]
        print(" | ".join(text))
    print()
    print("Validation Summary")
    print("1. preserve all notifications")
    print("2. govern only interruption visibility")
    print("3. ask the user only when structure is unknown")
    print("4. convert user decisions into reusable structural rules")
    print("5. activate learned rules only after maturity")
    print("6. block conflicted rules from automatic interruption")
    print("7. govern interruption through priority and budget")
    print("8. allow emergency override only when structurally safe")
    print("9. keep deterministic replay certificates for auditability")
    print("10. make every decision explainable through a complete reason chain")
    print("11. adapt visibility through deterministic policy profiles")
    print("12. compare profile behavior without changing event structure")
    print("13. measure personal attention load through a deterministic ledger")
    print("14. prove release readiness through deterministic smoke execution")


def main():
    parser = argparse.ArgumentParser(description="SNARE structural notification attention ledger demo")
    parser.add_argument("--input", default="", help="Optional CSV or JSON notification file for initial learning")
    parser.add_argument("--future_input", default="", help="Optional CSV or JSON notification file for future resolution")
    parser.add_argument("--decisions", default="", help="Optional CSV or JSON user decision file")
    parser.add_argument("--out_dir", default="OUT_SNARE_DEMO_v1_0", help="Output directory")
    parser.add_argument("--confidence_threshold", type=float, default=0.75, help="Minimum confidence required for automatic rule activation")
    parser.add_argument("--priority_threshold", type=int, default=70, help="Minimum priority required for interruption")
    parser.add_argument("--interruption_budget", type=int, default=2, help="Maximum visible interruptions allowed in the attention window")
    parser.add_argument("--policy_profile", default="FOCUS_MODE", help="Policy profile: DEFAULT, FOCUS_MODE, WORK_MODE, FAMILY_MODE, or SLEEP_MODE")
    parser.add_argument("--compare_profiles", action="store_true", help="Write and print multi-profile comparison across all supported profiles")
    args = parser.parse_args()

    initial_notifications = load_notifications(args.input, future=False)
    future_notifications = load_notifications(args.future_input, future=True)
    decisions = load_decisions(args.decisions)

    active_policy = canonical_policy(args.policy_profile)
    initial_results = [resolve_notification(n, policy_profile=active_policy) for n in initial_notifications]
    mature_rules = learn_rules(initial_notifications, initial_results, decisions, args.confidence_threshold)
    future_base_results = [resolve_notification(n, mature_rules, policy_profile=active_policy) for n in future_notifications]
    future_results = apply_attention_budget(future_base_results, args.interruption_budget, args.priority_threshold)
    profile_results = resolve_profile_set(future_notifications, mature_rules, args.interruption_budget, args.priority_threshold)
    comparison_rows = compare_profile_results(profile_results)
    ledger_rows = build_attention_ledger(profile_results)

    print_report(initial_results, mature_rules, future_results, comparison_rows, ledger_rows, args.confidence_threshold, args.priority_threshold, args.interruption_budget, active_policy)
    outputs = write_outputs(initial_results, future_results, mature_rules, comparison_rows, ledger_rows, args.out_dir)
    print("Outputs")
    print("Initial CSV : " + str(outputs[0]))
    print("Initial JSON: " + str(outputs[1]))
    print("Rules CSV   : " + str(outputs[2]))
    print("Rules JSON  : " + str(outputs[3]))
    print("Future CSV  : " + str(outputs[4]))
    print("Future JSON : " + str(outputs[5]))
    print("Compare CSV : " + str(outputs[6]))
    print("Compare JSON: " + str(outputs[7]))
    print("Ledger CSV  : " + str(outputs[8]))
    print("Ledger JSON : " + str(outputs[9]))


if __name__ == "__main__":
    main()
