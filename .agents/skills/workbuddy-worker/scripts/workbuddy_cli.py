#!/usr/bin/env python3
"""Invoke CodeBuddy or a local WorkBuddy ACP gateway, without taking over sessions."""
from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


LOCAL_HISTORY_TEXT_BUDGET = 200000


class WorkBuddyError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def redact(text: str, *secrets: str) -> str:
    for secret in secrets:
        if secret:
            text = text.replace(secret, '[REDACTED]')
    return re.sub(r'(?i)(bearer\s+)\S+', r'\1[REDACTED]', text)


def parse_native_result(stdout: str, stderr: str, returncode: int) -> dict:
    if re.search(r'Authentication (?:required|failed)', stderr, re.I):
        raise WorkBuddyError('auth_required', 'CLI requires login; exit code 0 is not a successful reply.')
    if returncode:
        raise WorkBuddyError('native_failed', f'CLI exited with code {returncode}; inspect the local CLI login/configuration.')
    try:
        result = json.loads(stdout)
    except (ValueError, TypeError):
        raise WorkBuddyError('invalid_result', 'CLI did not return a JSON result.') from None
    if not isinstance(result, dict) or result.get('is_error') or result.get('error'):
        raise WorkBuddyError('native_failed', 'CLI returned an error result.')
    if result.get('status') is not None and str(result['status']).upper() != 'SUCCESS':
        raise WorkBuddyError('native_failed', 'CLI explicitly reported a failed or unrecognized status.')
    if result.get('subtype') not in (None, 'success'):
        raise WorkBuddyError('native_incomplete', 'CLI did not finish successfully; do not automatically repeat the task.')
    response = result.get('result')
    if not isinstance(response, str) or not response.strip():
        raise WorkBuddyError('empty_response', 'CLI returned no task response.')
    return {'status': 'SUCCESS', 'transport': 'native', 'response': response,
            'session_id': result.get('session_id')}


def find_cli(explicit: str | None = None) -> str | None:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file() or not os.access(path, os.X_OK):
            raise WorkBuddyError('cli_not_found', 'Specified CLI is not an executable file.')
        return str(path)
    for name in ('codebuddy', 'cbc'):
        if found := shutil.which(name):
            return found
    for app in (Path('/Applications/WorkBuddy.app'), Path.home() / 'Applications/WorkBuddy.app'):
        path = app / 'Contents/Resources/app.asar.unpacked/cli/bin/codebuddy'
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    return None


def native_environment(cli: str, config_dir: str | None = None) -> dict:
    env = os.environ.copy()
    if (Path(cli).resolve().parent.parent / 'dist/codebuddy-lite-wb.mjs').is_file():
        env['CODEBUDDY_FORCE_LITE_WB_BUNDLE'] = '1'
    env['DISABLE_AUTOUPDATER'] = '1'
    if config_dir:
        env['CODEBUDDY_CONFIG_DIR'] = str(Path(config_dir).expanduser().resolve())
        env['WORKBUDDY_CONFIG_DIR'] = env['CODEBUDDY_CONFIG_DIR']
    return env


def run_native(cli: str, prompt: str, workspace: Path, session_id: str | None,
               mode: str, timeout: float, config_dir: str | None = None) -> dict:
    tools = 'Read' if mode == 'read' else 'Read,Write,Edit'
    args = [cli, '-p', prompt, '--output-format', 'json', '--tools', tools,
            '--allowedTools', tools, '--permission-mode', 'dontAsk',
            '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
            '--setting-sources', 'user', '--settings', '{"disableAllHooks":true}']
    if session_id:
        args += ['--resume', session_id]
    else:
        args += ['--session-id', str(uuid.uuid4())]
    try:
        process = subprocess.run(args, cwd=workspace, env=native_environment(cli, config_dir),
                                 capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise WorkBuddyError('delivery_unknown', 'CLI timed out. Task outcome is unknown; inspect the session before retrying.') from None
    except OSError:
        raise WorkBuddyError('cli_start_failed', 'Could not launch the selected CLI.') from None
    return parse_native_result(process.stdout, process.stderr, process.returncode)


@dataclass
class Gateway:
    url: str
    token: str = field(repr=False)
    pid: int | None = None

    def __post_init__(self):
        parsed = urllib.parse.urlsplit(self.url)
        try:
            port = parsed.port
        except ValueError:
            port = None
        if (parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost')
                or not port or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ('', '/')):
            raise WorkBuddyError('invalid_gateway', 'Gateway must be an HTTP loopback address with a port and no credentials/path.')
        if not self.token:
            raise WorkBuddyError('auth_required', 'Gateway authentication token is missing.')
        self.url = f'http://127.0.0.1:{port}'

    def public_info(self) -> dict:
        return {'url': self.url, 'pid': self.pid}


def process_output(args: list[str]) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        raise WorkBuddyError('discovery_failed', 'Could not inspect local WorkBuddy processes.') from None
    return result.stdout if result.returncode == 0 else ''


def discover_gateways() -> list[Gateway]:
    if sys.platform != 'darwin':
        return []
    apps = [str(p.resolve()) for p in (Path('/Applications/WorkBuddy.app'), Path.home() / 'Applications/WorkBuddy.app') if p.exists()]
    processes = process_output(['ps', '-axo', 'pid=,uid=,comm='])
    gateways = []
    for line in processes.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        if int(parts[1]) != os.getuid() or not any(parts[2] == app + '/Contents/MacOS/Electron' for app in apps):
            continue
        pid = int(parts[0])
        command = process_output(['ps', '-p', str(pid), '-o', 'command='])
        if not re.search(r'(?:^|\s)--serve(?:\s|$)', command):
            continue
        # The installed desktop passes this ephemeral password to its sidecar.
        # Capture it in memory only: never log or serialize the process environment.
        environment = process_output(['ps', 'eww', '-p', str(pid), '-o', 'command='])
        match = re.search(r'(?:^|\s)CODEBUDDY_GATEWAY_PASSWORD=(\S+)', environment)
        if not match:
            continue
        listeners = process_output(['/usr/sbin/lsof', '-nP', '-a', '-p', str(pid), '-iTCP', '-sTCP:LISTEN', '-Fn'])
        for port in re.findall(r'^n127\.0\.0\.1:(\d+)$', listeners, re.M):
            gateways.append(Gateway('http://127.0.0.1:' + port, match.group(1), pid))
    return gateways


def select_gateway(url: str | None, token_env: str) -> Gateway:
    if url and os.environ.get(token_env):
        return Gateway(url, os.environ[token_env])
    gateways = discover_gateways()
    if url:
        normalized = Gateway(url, 'validation-only').url
        gateways = [g for g in gateways if g.url == normalized]
    if not gateways:
        raise WorkBuddyError('gateway_not_found', 'No matching WorkBuddy gateway found; start WorkBuddy or supply --url and a token environment variable.')
    if len(gateways) != 1:
        addresses = ', '.join(g.url for g in gateways)
        raise WorkBuddyError('ambiguous_gateway', f'Multiple gateways found; select one with --url: {addresses}')
    return gateways[0]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


class ACPClient:
    def __init__(self, gateway: Gateway, timeout: float = 120):
        self.gateway = gateway
        self.timeout = timeout
        self.headers = {'Authorization': 'Bearer ' + gateway.token,
                        'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
        self.connection_id = None
        self.capabilities = {}
        self.sequence = 0
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def _request(self, payload: dict | None = None, method: str = 'POST', suffix: str = ''):
        req = urllib.request.Request(self.gateway.url + '/api/v1/acp' + suffix,
            data=json.dumps(payload).encode() if payload is not None else b'', headers=self.headers, method=method)
        try:
            return self.opener.open(req, timeout=self.timeout)
        except urllib.error.HTTPError as error:
            code = 'redirect_blocked' if 300 <= error.code < 400 else 'auth_required' if error.code in (401, 403) else 'gateway_http_error'
            raise WorkBuddyError(code, f'Gateway returned HTTP {error.code}.') from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise WorkBuddyError('connection_failed', 'Gateway connection failed; task delivery may be unknown after submission.') from None

    def __enter__(self):
        try:
            with self._request({}, suffix='/connect') as response:
                connection = json.load(response)
            self.connection_id = connection['connectionId']
            self.headers['acp-connection-id'] = self.connection_id
            if connection.get('sessionToken'):
                self.headers['acp-session-token'] = connection['sessionToken']
            result, _ = self.rpc('initialize', {'protocolVersion': 1,
                'clientCapabilities': {'fs': {'readTextFile': False, 'writeTextFile': False}, 'terminal': False},
                'clientInfo': {'name': 'loom-os-workbuddy-worker', 'version': '1'}})
            self.capabilities = result.get('agentCapabilities', {})
            return self
        except Exception:
            self.close()
            raise

    def close(self):
        if self.connection_id:
            try:
                with self._request(method='DELETE'):
                    pass
            except WorkBuddyError:
                pass
            finally:
                self.connection_id = None

    def __exit__(self, *_args):
        self.close()

    def rpc(self, method: str, params: dict) -> tuple[dict, list[dict]]:
        self.sequence += 1
        rid = f'workbuddy-worker-{self.sequence}'
        messages = []
        deadline = time.monotonic() + self.timeout
        with self._request({'jsonrpc': '2.0', 'id': rid, 'method': method, 'params': params}) as response:
            if 'text/event-stream' not in response.headers.get('Content-Type', ''):
                messages.append(json.load(response))
            else:
                data_lines = []
                total = 0
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise WorkBuddyError('delivery_unknown', 'ACP request timed out; inspect the session before retrying.')
                    sock = getattr(getattr(getattr(response, 'fp', None), 'raw', None), '_sock', None)
                    if sock:
                        sock.settimeout(remaining)
                    line = response.readline(1048577)
                    total += len(line)
                    if len(line) > 1048576 or total > 32 * 1048576:
                        raise WorkBuddyError('protocol_error', 'ACP event stream exceeded the bounded response size.')
                    if not line:
                        break
                    line = line.decode('utf-8').rstrip('\r\n')
                    if line.startswith('data:'):
                        data_lines.append(line[5:].lstrip(' '))
                    elif not line and data_lines:
                        message = json.loads('\n'.join(data_lines))
                        data_lines = []
                        messages.append(message)
                        if message.get('method') in ('session/request_permission', 'fs/read_text_file', 'fs/write_text_file', 'terminal/create'):
                            raise WorkBuddyError('client_action_required', 'Gateway requested client tools/approval; this helper does not grant them.')
                        if message.get('id') == rid and ('result' in message or 'error' in message):
                            break
        reply = next((m for m in messages if m.get('id') == rid and ('result' in m or 'error' in m)), None)
        if reply is None:
            raise WorkBuddyError('protocol_error', 'ACP response has no matching RPC result.')
        if 'error' in reply:
            error = reply['error']
            reason = error.get('data', {}).get('reason') if isinstance(error.get('data'), dict) else None
            code = 'writer_occupied' if reason == 'writer_occupied' else 'unsupported_method' if error.get('code') == -32601 else 'acp_error'
            message = redact(str(error.get('message', 'ACP failed')), self.gateway.token, self.headers.get('acp-session-token', ''))
            raise WorkBuddyError(code, message)
        if not isinstance(reply['result'], dict):
            raise WorkBuddyError('protocol_error', 'ACP result is not an object.')
        return reply['result'], messages

    def send(self, session_id: str, workspace: Path, prompt: str) -> dict:
        result, _ = self.rpc('session/load', {'sessionId': session_id, 'cwd': str(workspace), 'mcpServers': []})
        if result.get('sessionId') != session_id:
            raise WorkBuddyError('session_mismatch', 'Gateway did not load the requested session; no prompt was sent.')
        reply, messages = self.rpc('session/prompt', {'sessionId': session_id,
            'prompt': [{'type': 'text', 'text': prompt}]})
        return parse_acp_prompt(messages, reply, session_id)


def parse_acp_prompt(messages: list[dict], reply: dict, session_id: str) -> dict:
    meta = reply.get('_meta', {})
    outcome = meta.get('codebuddy.ai/outcome')
    if outcome is not None and str(outcome).upper() != 'SUCCESS':
        raise WorkBuddyError('acp_failed', 'ACP explicitly reported a failed or unrecognized outcome.')
    request_id = meta.get('codebuddy.ai/conversationRequestId') or meta.get('codebuddy.ai/requestId')
    if not request_id:
        raise WorkBuddyError('missing_request_id', 'Cannot separate this response from history without a request ID.')
    chunks, tools = [], []
    for message in messages:
        params = message.get('params', {})
        if params.get('sessionId') != session_id:
            continue
        update = params.get('update', {})
        tags = update.get('_meta', {})
        update_request_id = tags.get('codebuddy.ai/conversationRequestId') or tags.get('codebuddy.ai/requestId')
        if update_request_id != request_id:
            continue
        kind, content = update.get('sessionUpdate'), update.get('content', {})
        if kind in ('agent_message_chunk', 'assistant_message_chunk') and isinstance(content, dict) and content.get('type') == 'text':
            chunks.append(content.get('text', ''))
        if kind == 'tool_call':
            tools.append(tags.get('codebuddy.ai/toolName', update.get('title', 'unknown')))
    response = ''.join(chunks)
    if reply.get('stopReason') != 'end_turn' or not response.strip():
        raise WorkBuddyError('incomplete_response', 'ACP did not provide a completed current-request response; inspect the session before retrying.')
    return {'status': 'SUCCESS', 'transport': 'gateway', 'session_id': session_id,
            'request_id': request_id, 'response': response, 'tool_names': tools}


def _local_session_files(config_dir: Path, session_id: str | None = None):
    projects = config_dir.expanduser().resolve() / 'projects'
    if not projects.is_dir():
        raise WorkBuddyError('local_store_not_found', 'WorkBuddy projects directory does not exist; check --config-dir.')
    for project in sorted(projects.iterdir()):
        if project.is_symlink() or not project.is_dir():
            continue
        paths = [project / (session_id + '.jsonl')] if session_id else sorted(project.glob('*.jsonl'))
        for path in paths:
            # Do not follow project/session symlinks or descend into sub-agent logs.
            if path.is_file() and not path.is_symlink():
                yield path


def _timestamp_ms(value) -> float | None:
    try:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            milliseconds = float(value)
        elif isinstance(value, str):
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            milliseconds = parsed.timestamp() * 1000
        else:
            return None
        datetime.fromtimestamp(milliseconds / 1000, timezone.utc)
        return milliseconds
    except (ValueError, OverflowError, OSError):
        return None


def _iso_timestamp(milliseconds: float) -> str:
    return datetime.fromtimestamp(milliseconds / 1000, timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def _message_text(record: dict) -> str:
    if record.get('type') != 'message' or record.get('role') not in ('user', 'assistant'):
        return ''
    if any(record.get(key) is True for key in ('isMeta', 'isInjected', 'isHidden')):
        return ''
    content = record.get('content')
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return ''.join(block['text'] for block in content if isinstance(block, dict)
                       and block.get('type') in ('input_text', 'output_text', 'text')
                       and isinstance(block.get('text'), str))
    return ''


def _scan_local_transcript(path: Path, limit: int = 0, max_chars: int = 4000,
                           role: str = 'all') -> dict:
    session_id = path.stem
    summary = {'session_id': session_id, 'title': session_id, 'workspace': None,
               'message_count': 0, 'updated_at': None}
    messages = deque()
    retained_chars = 0
    total, skipped, latest = 0, 0, None
    # Snapshot the byte length: a growing live log must not make this read endless.
    with path.open('rb') as stream:
        stat = os.fstat(stream.fileno())
        remaining = stat.st_size
        while remaining > 0:
            line = stream.readline(min(remaining, 8 * 1024 * 1024 + 1))
            if not line:
                break
            remaining -= len(line)
            if len(line) > 8 * 1024 * 1024:
                raise WorkBuddyError('record_too_large', 'Local history contains a record over 8 MiB; no unbounded read was performed.')
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                skipped += 1
                continue
            if not isinstance(record, dict):
                skipped += 1
                continue
            if record.get('sessionId') not in (None, '', session_id):
                continue
            timestamp = _timestamp_ms(record.get('timestamp'))
            if timestamp is not None:
                latest = timestamp if latest is None else max(latest, timestamp)
            cwd = record.get('cwd')
            if isinstance(cwd, str) and Path(cwd).is_absolute():
                summary['workspace'] = str(Path(cwd).resolve())
            if record.get('type') == 'ai-title' and isinstance(record.get('aiTitle'), str) and record['aiTitle'].strip():
                summary['title'] = record['aiTitle'][:300]
            text = _message_text(record)
            if not text.strip():
                continue
            summary['message_count'] += 1
            if role != 'all' and record['role'] != role:
                continue
            total += 1
            if limit:
                snippet = text[:max_chars]
                while messages and (len(messages) >= limit or retained_chars + len(snippet) > LOCAL_HISTORY_TEXT_BUDGET):
                    retained_chars -= len(messages.popleft()['text'])
                messages.append({'id': record.get('id'), 'role': record['role'],
                                 'timestamp': _iso_timestamp(timestamp) if timestamp is not None else None,
                                 'text': snippet, 'truncated': len(text) > max_chars})
                retained_chars += len(snippet)
    summary['updated_at'] = _iso_timestamp(latest if latest is not None else stat.st_mtime * 1000)
    return {'session': summary, 'messages': list(messages), 'total': total,
            'skipped_records': skipped, 'warnings': ['Malformed or incomplete JSONL records were skipped.'] if skipped else []}


def _workspace_matches(cwd: str | None, workspace: Path | None) -> bool:
    if workspace is None:
        return True
    return cwd is not None and Path(cwd).resolve().is_relative_to(workspace.expanduser().resolve())


def _validate_local_options(limit: int, max_chars: int = 4000, role: str = 'all'):
    if not 1 <= limit <= 1000 or not 1 <= max_chars <= 100000 or role not in ('all', 'user', 'assistant'):
        raise WorkBuddyError('invalid_history_options', 'Limit must be 1–1000, max-chars 1–100000, and role all/user/assistant.')


def list_local_sessions(config_dir: Path, workspace: Path | None, limit: int = 20,
                        query: str = '') -> dict:
    _validate_local_options(limit)
    sessions, skipped, warnings = [], 0, []
    for path in _local_session_files(config_dir):
        result = _scan_local_transcript(path)
        session = result['session']
        if not _workspace_matches(session['workspace'], workspace):
            continue
        if query.casefold() not in (session['title'] + ' ' + (session['workspace'] or '') + ' ' + session['session_id']).casefold():
            continue
        sessions.append(session)
        skipped += result['skipped_records']
        warnings.extend(result['warnings'])
    sessions.sort(key=lambda item: (item['updated_at'], item['session_id']), reverse=True)
    return {'status': 'SUCCESS', 'source': 'local', 'read_only': True,
            'sessions': sessions[:limit], 'total': len(sessions), 'has_more': len(sessions) > limit,
            'skipped_records': skipped, 'warnings': sorted(set(warnings))}


def read_local_history(config_dir: Path, session_id: str, workspace: Path | None,
                       limit: int = 20, max_chars: int = 4000, role: str = 'all') -> dict:
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_:-]{0,127}', session_id):
        raise WorkBuddyError('invalid_session_id', 'Session ID must be a plain identifier, not a path or glob.')
    _validate_local_options(limit, max_chars, role)
    matches = []
    for path in _local_session_files(config_dir, session_id):
        result = _scan_local_transcript(path, limit, max_chars, role)
        if _workspace_matches(result['session']['workspace'], workspace):
            matches.append(result)
    if not matches:
        raise WorkBuddyError('session_not_found', 'No matching local session in this workspace; check the ID and workspace scope.')
    if len(matches) > 1:
        raise WorkBuddyError('ambiguous_session', 'This session ID appears in multiple projects; narrow --workspace instead of picking one.')
    result = matches[0]
    return {'status': 'SUCCESS', 'source': 'local', 'read_only': True, **result,
            'session_id': session_id, 'has_more': result['total'] > len(result['messages']),
            'text_budget_chars': LOCAL_HISTORY_TEXT_BUDGET}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    doctor = commands.add_parser('doctor', help='Inspect local CLI/gateways; sends no task/model prompt.')
    doctor.add_argument('--cli')
    native = commands.add_parser('native', help='Run a new or explicitly resumed CodeBuddy CLI session.')
    native.add_argument('--cli')
    native.add_argument('--config-dir')
    native.add_argument('--session-id', help='Resume this explicit session; omitted means a fresh UUID.')
    native.add_argument('--mode', choices=('read', 'edit'), default='read')
    gateway = commands.add_parser('gateway', help='Send to an explicit existing ACP session without takeover.')
    gateway.add_argument('--session-id', required=True)
    for command in (doctor, gateway):
        command.add_argument('--url', help='Loopback gateway URL; omit to discover on macOS.')
        command.add_argument('--token-env', default='WORKBUDDY_GATEWAY_TOKEN', help='Environment variable holding a supplied token; never pass a token as an argument.')
    for command in (native, gateway):
        prompts = command.add_mutually_exclusive_group(required=True)
        prompts.add_argument('--prompt')
        prompts.add_argument('--prompt-file', type=Path)
        command.add_argument('--workspace', type=Path, default=Path.cwd())
    for command in (doctor, native, gateway):
        command.add_argument('--timeout', type=float, default=120 if command != doctor else 10)
    sessions = commands.add_parser('sessions', help='List local WorkBuddy sessions without contacting a model or gateway.')
    sessions.add_argument('--query', default='', help='Filter session ID, title or workspace (not message bodies).')
    history = commands.add_parser('history', help='Read recent user/assistant text from one local session.')
    history.add_argument('--session-id', required=True)
    history.add_argument('--role', choices=('all', 'user', 'assistant'), default='all')
    history.add_argument('--max-chars', type=int, default=4000, help='Maximum characters per message (1–100000).')
    for command in (sessions, history):
        command.add_argument('--config-dir', type=Path, help='WorkBuddy data root; defaults to WORKBUDDY_CONFIG_DIR or ~/.workbuddy.')
        command.add_argument('--limit', type=int, default=20, help='Return up to this many sessions or latest matching messages (1–1000).')
        scope = command.add_mutually_exclusive_group()
        scope.add_argument('--workspace', type=Path, default=Path.cwd(), help='Include this workspace and descendants; default is current directory.')
        scope.add_argument('--all-workspaces', action='store_true', help='Explicitly allow reading across all local projects.')
    args = parser.parse_args()
    try:
        if args.command in ('sessions', 'history'):
            config_dir = args.config_dir or Path(os.environ.get('WORKBUDDY_CONFIG_DIR') or str(Path.home() / '.workbuddy'))
            scope = None if args.all_workspaces else args.workspace.expanduser().resolve()
            if args.command == 'sessions':
                output = list_local_sessions(config_dir, scope, args.limit, args.query)
            else:
                output = read_local_history(config_dir, args.session_id, scope, args.limit, args.max_chars, args.role)
        elif args.timeout <= 0:
            raise WorkBuddyError('invalid_timeout', 'Timeout must be positive.')
        elif args.command == 'doctor':
            cli = find_cli(args.cli)
            if args.url:
                candidates = [select_gateway(args.url, args.token_env)]
            else:
                candidates = discover_gateways()
            output = {'status': 'SUCCESS', 'cli': cli, 'gateways': [],
                      'note': 'Discovery/ACP initialization does not prove CLI login, session ownership or task success.'}
            for candidate in candidates:
                info = candidate.public_info()
                try:
                    with ACPClient(candidate, args.timeout) as client:
                        info.update({'acp_ready': True, 'capabilities': client.capabilities})
                except WorkBuddyError as error:
                    info.update({'acp_ready': False, 'error_code': error.code})
                output['gateways'].append(info)
        else:
            workspace = args.workspace.expanduser().resolve()
            if not workspace.is_dir():
                raise WorkBuddyError('invalid_workspace', 'Workspace must be an existing directory.')
            prompt = args.prompt if args.prompt is not None else args.prompt_file.read_text(encoding='utf-8')
            if not prompt.strip():
                raise WorkBuddyError('empty_prompt', 'Prompt must not be empty.')
            if args.command == 'native':
                cli = find_cli(args.cli)
                if not cli:
                    raise WorkBuddyError('cli_not_found', 'Install/configure CodeBuddy or specify --cli.')
                output = run_native(cli, prompt, workspace, args.session_id, args.mode, args.timeout, args.config_dir)
            else:
                with ACPClient(select_gateway(args.url, args.token_env), args.timeout) as client:
                    output = client.send(args.session_id, workspace, prompt)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except WorkBuddyError as error:
        print(json.dumps({'status': 'ERROR', 'error_code': error.code, 'error': str(error)}, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({'status': 'ERROR', 'error_code': 'protocol_or_io_error',
                          'error': 'Invalid response or local I/O failure; task outcome may be unknown.'}))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
