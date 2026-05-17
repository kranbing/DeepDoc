from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from backend.services.project_store import write_json as write_data_json
from backend.services.qa_service import compact_session_with_deepseek


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_qa_sessions_state() -> Dict[str, Any]:
    return {
        "sessions": [],
        "updatedAt": utc_now(),
    }


def default_qa_compactions_state() -> Dict[str, Any]:
    return {
        "sessions": {},
        "updatedAt": utc_now(),
    }


def _conversations_dir(project_dir: Path) -> Path:
    return project_dir / "conversations"


def _sessions_root(project_dir: Path) -> Path:
    return _conversations_dir(project_dir) / "sessions"


def _session_dir(project_dir: Path, session_id: str) -> Path:
    return _sessions_root(project_dir) / session_id


def _session_file(project_dir: Path, session_id: str) -> Path:
    return _session_dir(project_dir, session_id) / "session.json"


def _summary_file(project_dir: Path, session_id: str) -> Path:
    return _session_dir(project_dir, session_id) / "summary.json"


def _session_index_file(project_dir: Path) -> Path:
    return _sessions_root(project_dir) / "index.json"


def _session_index_entry(session: Dict[str, Any]) -> Dict[str, Any]:
    turns = session.get("turns") if isinstance(session.get("turns"), list) else []
    return {
        "id": str(session.get("id") or ""),
        "docId": session.get("docId"),
        "docName": session.get("docName"),
        "startedAt": session.get("startedAt"),
        "updatedAt": session.get("updatedAt"),
        "turnCount": len(turns),
    }


def _read_json_file(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _write_json_file(path: Path, payload: Any) -> None:
    write_data_json(path, payload)


def _migrate_legacy_session_storage(project_dir: Path) -> None:
    sessions_root = _sessions_root(project_dir)
    index_path = _session_index_file(project_dir)
    legacy_sessions_path = _conversations_dir(project_dir) / "qa_sessions.json"
    legacy_compactions_path = _conversations_dir(project_dir) / "qa_compactions.json"
    if index_path.is_file() or not legacy_sessions_path.is_file():
        sessions_root.mkdir(parents=True, exist_ok=True)
        return

    legacy_store = _read_json_file(legacy_sessions_path, default_qa_sessions_state())
    legacy_sessions = legacy_store.get("sessions") if isinstance(legacy_store.get("sessions"), list) else []
    compaction_store = _read_json_file(legacy_compactions_path, default_qa_compactions_state())
    legacy_compactions = compaction_store.get("sessions") if isinstance(compaction_store.get("sessions"), dict) else {}
    migrated_entries: List[Dict[str, Any]] = []
    sessions_root.mkdir(parents=True, exist_ok=True)
    for raw_session in legacy_sessions:
        if not isinstance(raw_session, dict):
            continue
        session = dict(raw_session)
        session_id = str(session.get("id") or "").strip() or f"qa_{uuid.uuid4().hex[:12]}"
        session["id"] = session_id
        _write_json_file(_session_file(project_dir, session_id), session)
        summary = legacy_compactions.get(session_id)
        if isinstance(summary, dict):
            _write_json_file(_summary_file(project_dir, session_id), summary)
        migrated_entries.append(_session_index_entry(session))
    migrated_entries.sort(key=lambda item: str(item.get("updatedAt") or item.get("startedAt") or ""), reverse=True)
    _write_json_file(index_path, {"sessions": migrated_entries, "updatedAt": utc_now()})
    legacy_sessions_path.rename(legacy_sessions_path.with_suffix(".legacy.json"))
    if legacy_compactions_path.is_file():
        legacy_compactions_path.rename(legacy_compactions_path.with_suffix(".legacy.json"))


def read_qa_sessions(project_dir: Path) -> Dict[str, Any]:
    _migrate_legacy_session_storage(project_dir)
    index = _read_json_file(_session_index_file(project_dir), default_qa_sessions_state())
    base = default_qa_sessions_state()
    if isinstance(index, dict):
        base.update(index)
    entries = base.get("sessions") if isinstance(base.get("sessions"), list) else []
    sessions: List[Dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        session_id = str(entry.get("id") or "").strip()
        if not session_id:
            continue
        session = _read_json_file(_session_file(project_dir, session_id), {})
        if isinstance(session, dict) and session:
            sessions.append(session)
    base["sessions"] = sessions
    return base


def write_qa_sessions(project_dir: Path, state: Dict[str, Any]) -> None:
    sessions_root = _sessions_root(project_dir)
    sessions_root.mkdir(parents=True, exist_ok=True)
    state = dict(state)
    state["updatedAt"] = utc_now()
    sessions = state.get("sessions") if isinstance(state.get("sessions"), list) else []
    index_entries: List[Dict[str, Any]] = []
    active_ids: Set[str] = set()
    for session in sessions:
        if not isinstance(session, dict):
            continue
        session_id = str(session.get("id") or "").strip()
        if not session_id:
            continue
        active_ids.add(session_id)
        _write_json_file(_session_file(project_dir, session_id), session)
        index_entries.append(_session_index_entry(session))
    for child in sessions_root.iterdir():
        if child.is_dir() and child.name not in active_ids:
            shutil.rmtree(child, ignore_errors=True)
    index_entries.sort(key=lambda item: str(item.get("updatedAt") or item.get("startedAt") or ""), reverse=True)
    _write_json_file(_session_index_file(project_dir), {"sessions": index_entries, "updatedAt": state["updatedAt"]})


def read_qa_compactions(project_dir: Path) -> Dict[str, Any]:
    _migrate_legacy_session_storage(project_dir)
    base = default_qa_compactions_state()
    sessions: Dict[str, Any] = {}
    sessions_root = _sessions_root(project_dir)
    if sessions_root.is_dir():
        for child in sessions_root.iterdir():
            if not child.is_dir():
                continue
            summary = _read_json_file(child / "summary.json", None)
            if isinstance(summary, dict):
                sessions[child.name] = summary
    base["sessions"] = sessions
    return base


def write_qa_compactions(project_dir: Path, state: Dict[str, Any]) -> None:
    sessions_root = _sessions_root(project_dir)
    sessions_root.mkdir(parents=True, exist_ok=True)
    state = dict(state)
    state["updatedAt"] = utc_now()
    sessions_map = state.get("sessions") if isinstance(state.get("sessions"), dict) else {}
    for session_id, summary in sessions_map.items():
        if not isinstance(summary, dict):
            continue
        _write_json_file(_summary_file(project_dir, str(session_id)), summary)


def append_qa_turn(
    project_dir: Path,
    session_id: str,
    doc_id: str,
    doc_name: str,
    question: str,
    result: Dict[str, Any],
) -> Dict[str, Any]:
    store = read_qa_sessions(project_dir)
    sessions = store.get("sessions") if isinstance(store.get("sessions"), list) else []
    now_iso = utc_now()
    chunk_context = result.get("chunk_context") if isinstance(result.get("chunk_context"), dict) else None
    turn = {
        "askedAt": now_iso,
        "docId": doc_id,
        "docName": doc_name,
        "question": question,
        "answer": result.get("answer", ""),
        "citedChunkIds": result.get("cited_chunk_ids", []),
        "followUpQuestions": result.get("follow_up_questions", []),
        "chunkContext": chunk_context,
    }
    target: Optional[Dict[str, Any]] = None
    for session in sessions:
        if isinstance(session, dict) and str(session.get("id") or "") == session_id:
            target = session
            break
    if target is None:
        target = {
            "id": session_id,
            "startedAt": now_iso,
            "updatedAt": now_iso,
            "docId": doc_id,
            "docName": doc_name,
            "turns": [],
            "suggestions": [],
        }
        sessions.append(target)
    turns = target.get("turns") if isinstance(target.get("turns"), list) else []
    turns.append(turn)
    target["turns"] = turns
    target["updatedAt"] = now_iso
    target["docId"] = doc_id
    target["docName"] = doc_name
    target["suggestions"] = result.get("follow_up_questions", [])
    store["sessions"] = sessions
    write_qa_sessions(project_dir, store)
    return target


def _session_messages(session: Dict[str, Any]) -> List[Dict[str, Any]]:
    turns = session.get("turns") if isinstance(session.get("turns"), list) else []
    messages: List[Dict[str, Any]] = []
    for idx, turn in enumerate(turns):
        if not isinstance(turn, dict):
            continue
        asked_at = str(turn.get("askedAt") or session.get("updatedAt") or "")
        question = str(turn.get("question") or "").strip()
        answer = str(turn.get("answer") or "").strip()
        if question:
            messages.append(
                {
                    "id": f"{session.get('id', 'session')}_u_{idx}",
                    "role": "user",
                    "text": question,
                    "timestamp": asked_at,
                    "chunkContext": turn.get("chunkContext"),
                }
            )
        if answer:
            messages.append(
                {
                    "id": f"{session.get('id', 'session')}_a_{idx}",
                    "role": "assistant",
                    "text": answer,
                    "timestamp": asked_at,
                    "citedChunkIds": turn.get("citedChunkIds", []),
                    "chunkContext": turn.get("chunkContext"),
                }
            )
    return messages


def _session_title(session: Dict[str, Any]) -> str:
    turns = session.get("turns") if isinstance(session.get("turns"), list) else []
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        question = str(turn.get("question") or "").strip()
        if question:
            short = question.replace("\n", " ").strip()
            return short[:28] + ("..." if len(short) > 28 else "")
    return f"新对话 {str(session.get('startedAt') or '')[:10] or '未命名'}"


def session_recent_turns(session: Dict[str, Any], limit: int = 4) -> List[Dict[str, Any]]:
    turns = session.get("turns") if isinstance(session.get("turns"), list) else []
    out: List[Dict[str, Any]] = []
    for turn in turns[-limit:]:
        if not isinstance(turn, dict):
            continue
        question = str(turn.get("question") or "").strip()
        answer = str(turn.get("answer") or "").strip()
        if question:
            out.append({"role": "user", "text": question})
        if answer:
            out.append({"role": "assistant", "text": answer})
    return out


def serialize_session(session: Dict[str, Any], compaction: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "id": str(session.get("id") or ""),
        "docId": session.get("docId"),
        "docName": session.get("docName"),
        "startedAt": session.get("startedAt"),
        "updatedAt": session.get("updatedAt"),
        "title": _session_title(session),
        "messages": _session_messages(session),
        "suggestions": session.get("suggestions") if isinstance(session.get("suggestions"), list) else [],
        "turnCount": len(session.get("turns") if isinstance(session.get("turns"), list) else []),
        "compaction": compaction if isinstance(compaction, dict) else None,
    }


def list_doc_sessions(project_dir: Path, doc_id: str) -> List[Dict[str, Any]]:
    store = read_qa_sessions(project_dir)
    sessions = store.get("sessions") if isinstance(store.get("sessions"), list) else []
    compactions = read_qa_compactions(project_dir).get("sessions")
    compaction_map = compactions if isinstance(compactions, dict) else {}
    filtered = [
        session
        for session in sessions
        if isinstance(session, dict) and str(session.get("docId") or "") == doc_id
    ]
    filtered.sort(key=lambda item: str(item.get("updatedAt") or item.get("startedAt") or ""), reverse=True)
    return [
        serialize_session(session, compaction_map.get(str(session.get("id") or "")))
        for session in filtered
    ]


def create_session(project_dir: Path, doc_id: str, doc_name: str) -> Dict[str, Any]:
    store = read_qa_sessions(project_dir)
    sessions = store.get("sessions") if isinstance(store.get("sessions"), list) else []
    session = {
        "id": f"qa_{uuid.uuid4().hex[:12]}",
        "startedAt": utc_now(),
        "updatedAt": utc_now(),
        "docId": doc_id,
        "docName": doc_name,
        "turns": [],
        "suggestions": [],
    }
    sessions.append(session)
    store["sessions"] = sessions
    write_qa_sessions(project_dir, store)
    return session


def get_session(project_dir: Path, session_id: str) -> Optional[Dict[str, Any]]:
    store = read_qa_sessions(project_dir)
    sessions = store.get("sessions") if isinstance(store.get("sessions"), list) else []
    for session in sessions:
        if isinstance(session, dict) and str(session.get("id") or "") == session_id:
            return session
    return None


def ensure_active_session(
    project_dir: Path,
    doc_id: str,
    doc_name: str,
    *,
    active_doc_id: str = "",
    active_session_id: str = "",
) -> Dict[str, Any]:
    session = get_session(project_dir, active_session_id) if active_session_id else None
    if (
        isinstance(session, dict)
        and str(session.get("docId") or "") == doc_id
        and active_doc_id == doc_id
    ):
        return session
    return create_session(project_dir, doc_id, doc_name)


def compact_session_if_needed(root: Path, project_dir: Path, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    turns = session.get("turns") if isinstance(session.get("turns"), list) else []
    if len(turns) < 8:
        return None
    raw_chars = sum(
        len(str(turn.get("question") or "")) + len(str(turn.get("answer") or ""))
        for turn in turns
        if isinstance(turn, dict)
    )
    if raw_chars < 12000 and len(turns) < 10:
        return None
    store = read_qa_compactions(project_dir)
    sessions_map = store.get("sessions") if isinstance(store.get("sessions"), dict) else {}
    if not isinstance(sessions_map, dict):
        sessions_map = {}
    session_id = str(session.get("id") or "")
    existing = sessions_map.get(session_id)
    if isinstance(existing, dict) and int(existing.get("sourceTurnCount") or 0) >= len(turns):
        return existing

    transcript_parts: List[str] = []
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        question = str(turn.get("question") or "").strip()
        answer = str(turn.get("answer") or "").strip()
        if question:
            transcript_parts.append(f"user: {question}")
        if answer:
            transcript_parts.append(f"assistant: {answer}")

    compacted = compact_session_with_deepseek(
        root,
        transcript_parts,
        raw_char_count=raw_chars,
        turn_count=len(turns),
    )
    compacted["updatedAt"] = utc_now()
    sessions_map[session_id] = compacted
    store["sessions"] = sessions_map
    write_qa_compactions(project_dir, store)
    return compacted
