"""Offline regressions for the WorkBuddy process and ACP boundaries."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import workbuddy_cli as wb


class GatewayServer:
    def __init__(self, locked=False, wrong_session=False, redirect=False):
        self.locked = locked
        self.wrong_session = wrong_session
        self.redirect = redirect
        self.calls = []
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def respond(self, body, status=200, mime='application/json'):
                raw = body.encode() if isinstance(body, str) else json.dumps(body).encode()
                self.send_response(status)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
                parent.calls.append(body.get('method', 'connect'))
                if self.headers.get('Authorization') != 'Bearer test-secret':
                    self.respond({'error': 'unauthorized'}, 401)
                    return
                if parent.redirect:
                    self.send_response(302)
                    self.send_header('Location', 'http://example.com/not-local')
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                if self.path.endswith('/connect'):
                    self.respond({'connectionId': 'test-connection', 'sessionToken': 'test-session-token'})
                    return
                method = body['method']
                if method == 'initialize':
                    self.respond({'jsonrpc': '2.0', 'id': body['id'], 'result': {'protocolVersion': 1}})
                elif method == 'session/load':
                    if parent.locked:
                        self.respond({'jsonrpc': '2.0', 'id': body['id'], 'error': {
                            'code': -32000, 'message': 'Persistent Session already has an external writer',
                            'data': {'reason': 'writer_occupied'}}})
                    else:
                        self.respond({'jsonrpc': '2.0', 'id': body['id'], 'result': {
                            'sessionId': 'wrong-session' if parent.wrong_session else body['params']['sessionId']}})
                elif method == 'session/prompt':
                    events = [
                        {'method': 'session/update', 'params': {'sessionId': 'target', 'update': {
                            'sessionUpdate': 'agent_message_chunk', 'content': {'type': 'text', 'text': 'old private history'},
                            '_meta': {'codebuddy.ai/requestId': 'old-request'}}}},
                        {'method': 'session/update', 'params': {'sessionId': 'target', 'update': {
                            'sessionUpdate': 'agent_message_chunk', 'content': {'type': 'text', 'text': 'fresh answer'},
                            '_meta': {'codebuddy.ai/conversationRequestId': 'new-request'}}}},
                        {'jsonrpc': '2.0', 'id': body['id'], 'result': {'stopReason': 'end_turn',
                            '_meta': {'codebuddy.ai/conversationRequestId': 'new-request'}}},
                    ]
                    self.respond(''.join('event: message\ndata: ' + json.dumps(x) + '\n\n' for x in events),
                                 mime='text/event-stream')
                else:
                    self.respond({'jsonrpc': '2.0', 'id': body['id'], 'error': {'code': -32601, 'message': 'Method not found'}})

            def do_DELETE(self):
                parent.calls.append('close')
                self.send_response(204)
                self.end_headers()

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    @property
    def gateway(self):
        return wb.Gateway(f'http://127.0.0.1:{self.server.server_port}', 'test-secret')


class NativeResultTests(unittest.TestCase):
    def test_zero_exit_with_auth_error_is_failure(self):
        with self.assertRaises(wb.WorkBuddyError) as raised:
            wb.parse_native_result('', 'Authentication required. Please use /login', 0)
        self.assertEqual(raised.exception.code, 'auth_required')

    def test_invalid_json_is_not_a_success(self):
        with self.assertRaises(wb.WorkBuddyError):
            wb.parse_native_result('started successfully', '', 0)

    def test_error_result_is_not_a_success(self):
        with self.assertRaises(wb.WorkBuddyError):
            wb.parse_native_result(json.dumps({'is_error': True, 'result': 'failed'}), '', 0)

    def test_explicit_failed_status_is_not_a_success(self):
        with self.assertRaises(wb.WorkBuddyError):
            wb.parse_native_result(json.dumps({'status': 'ERROR', 'result': 'failure details'}), '', 0)

    def test_native_result_returns_response_and_session(self):
        result = wb.parse_native_result(json.dumps({'is_error': False, 'result': 'done', 'session_id': 'native-session'}), '', 0)
        self.assertEqual(result['response'], 'done')
        self.assertEqual(result['session_id'], 'native-session')

    def test_native_resume_uses_explicit_session_and_read_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            cli = Path(tmp) / 'fake-cli'
            cli.write_text('#!/usr/bin/env python3\nimport sys,json\nprint(json.dumps({"is_error":False,"result":json.dumps(sys.argv[1:]),"session_id":"native-session"}))\n')
            cli.chmod(0o700)
            result = wb.run_native(str(cli), 'hello', Path(tmp), 'known-session', 'read', 5)
            args = json.loads(result['response'])
            self.assertIn('--resume', args)
            self.assertEqual(args[args.index('--resume') + 1], 'known-session')
            self.assertNotIn('--continue', args)
            self.assertEqual(args[args.index('--tools') + 1], 'Read')
            self.assertNotIn('--dangerously-skip-permissions', args)


class ACPTests(unittest.TestCase):
    def test_writer_lock_stops_before_any_prompt(self):
        with GatewayServer(locked=True) as server:
            with self.assertRaises(wb.WorkBuddyError) as raised:
                with wb.ACPClient(server.gateway, 5) as client:
                    client.send('target', Path.cwd(), 'hello')
            self.assertEqual(raised.exception.code, 'writer_occupied')
            self.assertNotIn('session/prompt', server.calls)
            self.assertNotIn('session/new', server.calls)
            self.assertIn('close', server.calls)

    def test_sse_history_is_excluded_from_prompt_result(self):
        with GatewayServer() as server:
            with wb.ACPClient(server.gateway, 5) as client:
                result = client.send('target', Path.cwd(), 'hello')
            self.assertEqual(result['response'], 'fresh answer')
            self.assertEqual(result['request_id'], 'new-request')
            self.assertEqual(server.calls, ['connect', 'initialize', 'session/load', 'session/prompt', 'close'])

    def test_session_mismatch_stops_before_prompt(self):
        with GatewayServer(wrong_session=True) as server:
            with self.assertRaises(wb.WorkBuddyError):
                with wb.ACPClient(server.gateway, 5) as client:
                    client.send('target', Path.cwd(), 'hello')
            self.assertNotIn('session/prompt', server.calls)

    def test_redirect_does_not_forward_local_token(self):
        with GatewayServer(redirect=True) as server:
            with self.assertRaises(wb.WorkBuddyError) as raised:
                with wb.ACPClient(server.gateway, 5):
                    pass
            self.assertEqual(raised.exception.code, 'redirect_blocked')
            self.assertNotIn('test-secret', str(raised.exception))

    def test_external_gateway_is_rejected(self):
        with self.assertRaises(wb.WorkBuddyError):
            wb.Gateway('https://example.com', 'private-token')

    def test_token_is_not_in_gateway_repr(self):
        self.assertNotIn('private-token', repr(wb.Gateway('http://127.0.0.1:1234', 'private-token')))

    def test_missing_request_id_never_falls_back_to_history(self):
        with self.assertRaises(wb.WorkBuddyError):
            wb.parse_acp_prompt([{'params': {'update': {'sessionUpdate': 'agent_message_chunk',
                'content': {'type': 'text', 'text': 'old history'}}}}], {'stopReason': 'end_turn'}, 'target')

    def test_explicit_failed_acp_outcome_is_not_a_success(self):
        update = {'params': {'sessionId': 'target', 'update': {'sessionUpdate': 'agent_message_chunk',
            'content': {'type': 'text', 'text': 'failure details'}, '_meta': {'codebuddy.ai/requestId': 'current'}}}}
        with self.assertRaises(wb.WorkBuddyError):
            wb.parse_acp_prompt([update], {'stopReason': 'end_turn',
                '_meta': {'codebuddy.ai/requestId': 'current', 'codebuddy.ai/outcome': 'ERROR'}}, 'target')

    def test_historical_conversation_id_wins_over_shared_request_id(self):
        updates = [{'params': {'sessionId': 'target', 'update': {'sessionUpdate': 'agent_message_chunk',
            'content': {'type': 'text', 'text': text}, '_meta': {
                'codebuddy.ai/conversationRequestId': conversation, 'codebuddy.ai/requestId': 'current'}}}}
            for conversation, text in [('old-conversation', 'old history'), ('current', 'fresh answer')]]
        result = wb.parse_acp_prompt(updates, {'stopReason': 'end_turn',
            '_meta': {'codebuddy.ai/conversationRequestId': 'current'}}, 'target')
        self.assertEqual(result['response'], 'fresh answer')

    def test_foreign_session_events_are_excluded(self):
        updates = [{'params': {'sessionId': sid, 'update': {'sessionUpdate': 'agent_message_chunk',
            'content': {'type': 'text', 'text': text}, '_meta': {'codebuddy.ai/requestId': 'current'}}}}
            for sid, text in [('someone-else', 'private'), ('target', 'expected')]]
        result = wb.parse_acp_prompt(updates, {'stopReason': 'end_turn',
            '_meta': {'codebuddy.ai/requestId': 'current'}}, 'target')
        self.assertEqual(result['response'], 'expected')


if __name__ == '__main__':
    unittest.main()
