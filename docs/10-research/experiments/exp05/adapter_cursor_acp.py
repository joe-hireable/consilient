"""EXP-05 adapter: Cursor controlled through its native ACP server.

Cursor consumes MCP servers as tools. Its supported external control surface is
Agent Client Protocol (ACP): newline-delimited JSON-RPC over stdio. Keeping that
direction explicit prevents an MCP tool bridge from being mistaken for Cursor's
native protocol.
"""

import json
import queue
import shutil
import subprocess
import threading
import time

from adapter_cursor import model_fields, to_wsl_path, usage_fields

WSL = shutil.which("wsl")
GIT = shutil.which("git")
CURSOR_WSL = "/home/jpbpr/.local/bin/cursor-agent"

KNOWN_SUCCESS_STOP_REASONS = {"end_turn", "stop", "completed", "complete"}


def is_success_stop_reason(stop_reason):
    """Fail closed unless stopReason is one of the explicit success reasons."""
    return stop_reason in KNOWN_SUCCESS_STOP_REASONS


class CursorAcpClient:
    """Small ACP v1 client for one experimental Cursor session."""

    def __init__(self, timeout_s):
        if not WSL:
            raise RuntimeError("wsl not found; Cursor CLI is linux/darwin only")
        self.timeout_s = timeout_s
        self.next_id = 1
        self.messages = []
        self.permissions = []
        self.stderr = []
        self.stdout_queue = queue.Queue()
        self.proc = subprocess.Popen(
            [
                WSL,
                "-d",
                "Ubuntu",
                "--",
                CURSOR_WSL,
                "acp",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        threading.Thread(
            target=self._read_stdout, name="cursor-acp-stdout", daemon=True
        ).start()
        threading.Thread(
            target=self._read_stderr, name="cursor-acp-stderr", daemon=True
        ).start()

    def _read_stdout(self):
        for line in self.proc.stdout:
            self.stdout_queue.put(line)

    def _read_stderr(self):
        for line in self.proc.stderr:
            self.stderr.append(line)

    def _write(self, message):
        if self.proc.poll() is not None:
            raise RuntimeError(f"Cursor ACP exited with {self.proc.returncode}")
        self.proc.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()

    def _respond(self, request_id, result):
        self._write({"jsonrpc": "2.0", "id": request_id, "result": result})

    def _handle_agent_request(self, message):
        method = message.get("method")
        if method == "session/request_permission":
            params = message.get("params") or {}
            self.permissions.append(params)
            self._respond(
                message["id"],
                {"outcome": {"outcome": "selected", "optionId": "allow-once"}},
            )
            return
        if method == "cursor/create_plan":
            self._respond(message["id"], {"outcome": {"outcome": "accepted"}})
            return
        if method == "cursor/ask_question":
            self._respond(
                message["id"],
                {"outcome": {"outcome": "skipped", "reason": "headless experiment"}},
            )
            return
        self._write(
            {
                "jsonrpc": "2.0",
                "id": message["id"],
                "error": {"code": -32601, "message": f"Unsupported method: {method}"},
            }
        )

    def request(self, method, params):
        request_id = self.next_id
        self.next_id += 1
        self._write(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params,
            }
        )
        deadline = time.monotonic() + self.timeout_s
        while time.monotonic() < deadline:
            try:
                line = self.stdout_queue.get(timeout=min(1, deadline - time.monotonic()))
            except queue.Empty:
                if self.proc.poll() is not None:
                    raise RuntimeError(f"Cursor ACP exited with {self.proc.returncode}")
                continue
            message = json.loads(line)
            self.messages.append(message)
            if message.get("id") == request_id and (
                "result" in message or "error" in message
            ):
                if "error" in message:
                    raise RuntimeError(f"Cursor ACP {method}: {message['error']}")
                return message["result"]
            if "id" in message and "method" in message:
                self._handle_agent_request(message)
        raise TimeoutError(f"Cursor ACP {method} timed out after {self.timeout_s}s")

    def close(self):
        if self.proc.stdin:
            self.proc.stdin.close()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            self.proc.wait(timeout=5)


def agent_text(messages):
    chunks = []
    for message in messages:
        if message.get("method") != "session/update":
            continue
        update = (message.get("params") or {}).get("update") or {}
        if update.get("sessionUpdate") != "agent_message_chunk":
            continue
        text = (update.get("content") or {}).get("text")
        if text:
            chunks.append(text)
    return "".join(chunks)


def parse_acp_outcome(
    ticket_id,
    session,
    result,
    requested_model,
    diff,
    duration_s,
    raw_tail,
):
    """Assemble the normalized ACP outcome dictionary."""
    session = session if isinstance(session, dict) else {}
    result = result if isinstance(result, dict) else {}

    stop_reason = (
        result.get("stopReason")
        if "stopReason" in result
        else result.get("stop_reason")
    )
    ok = is_success_stop_reason(stop_reason)

    session_id = session.get("sessionId") or session.get("session_id")
    request_id = result.get("requestId") or result.get("request_id")

    usage = usage_fields(result)
    models = model_fields(requested_model, result)
    if models["model_selected"] is None and "model" in session:
        models["model_selected"] = session.get("model")
        if requested_model is None:
            models["model"] = session.get("model")

    agent_name = f"cursor-acp:{requested_model}" if requested_model else "cursor-acp"

    return {
        "ticket_id": ticket_id,
        "agent": agent_name,
        "domain": "coding",
        "harness": "cursor",
        "provider": "cursor-subscription",
        **models,
        "control_protocol": "acp-v1-stdio",
        "session_id": session_id,
        "request_id": request_id,
        "stop_reason": stop_reason,
        "ok": ok,
        "diff": diff,
        **usage,
        "cost_usd": None,
        "duration_s": round(duration_s, 1),
        "raw_tail": raw_tail,
    }


def run(ticket, model=None):
    t0 = time.time()
    requested_model = model or ticket.get("model")
    client = CursorAcpClient(ticket.get("timeout_s", 600))
    session = {}
    result = {}
    try:
        client.request(
            "initialize",
            {
                "protocolVersion": 1,
                "clientCapabilities": {
                    "fs": {"readTextFile": False, "writeTextFile": False},
                    "terminal": False,
                },
                "clientInfo": {"name": "consilience-exp05", "version": "0.1.0"},
            },
        )
        client.request("authenticate", {"methodId": "cursor_login"})
        session_params = {"cwd": to_wsl_path(ticket["repo_dir"]), "mcpServers": []}
        if requested_model:
            session_params["model"] = requested_model
        session = client.request("session/new", session_params)
        result = client.request(
            "session/prompt",
            {
                "sessionId": session["sessionId"],
                "prompt": [{"type": "text", "text": ticket["goal"]}],
            },
        )
    finally:
        client.close()

    duration = time.time() - t0
    diff = subprocess.run(
        [GIT, "diff"],
        cwd=ticket["repo_dir"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    transcript = agent_text(client.messages)
    raw_tail = json.dumps(
        {
            "result": result,
            "permissions": client.permissions,
            "agent_text": transcript,
            "stderr": "".join(client.stderr)[-500:],
        },
        separators=(",", ":"),
    )[-1000:]

    return parse_acp_outcome(
        ticket_id=ticket["id"],
        session=session,
        result=result,
        requested_model=requested_model,
        diff=diff,
        duration_s=duration,
        raw_tail=raw_tail,
    )
