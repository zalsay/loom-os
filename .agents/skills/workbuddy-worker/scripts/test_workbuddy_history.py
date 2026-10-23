"""Read-only local history regressions; no WorkBuddy process or account required."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import workbuddy_cli as wb


class LocalHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / 'workbuddy'
        (self.config / 'projects').mkdir(parents=True)
        self.workspace = self.root / 'loom-os'
        self.workspace.mkdir()

    def transcript(self, sid='session-one', project='project-one', workspace=None, records=None):
        directory = self.config / 'projects' / project
        directory.mkdir(exist_ok=True)
        path = directory / (sid + '.jsonl')
        if records is None:
            records = [
                {'type': 'message', 'id': 'user-1', 'sessionId': sid,
                 'cwd': str(workspace or self.workspace), 'timestamp': 1000,
                 'role': 'user', 'content': [{'type': 'input_text', 'text': '请整理织界宣传计划'}]},
                {'type': 'message', 'id': 'assistant-1', 'sessionId': sid,
                 'cwd': str(workspace or self.workspace), 'timestamp': 2000,
                 'role': 'assistant', 'content': [{'type': 'output_text', 'text': '已整理课程定位'}]},
                {'type': 'ai-title', 'sessionId': sid, 'timestamp': 3000, 'aiTitle': '织界宣传协作'},
            ]
        path.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in records))
        return path

    def list_sessions(self, **kwargs):
        return wb.list_local_sessions(self.config, self.workspace, **kwargs)

    def history(self, sid='session-one', **kwargs):
        return wb.read_local_history(self.config, sid, self.workspace, **kwargs)

    def cli(self, *args):
        script = Path(wb.__file__).resolve()
        return subprocess.run([sys.executable, '-B', str(script), *args,
                               '--config-dir', str(self.config), '--workspace', str(self.workspace)],
                              capture_output=True, text=True, timeout=10)

    def test_lists_metadata_without_dumping_conversation(self):
        self.transcript()
        result = self.list_sessions()
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertEqual(result['source'], 'local')
        self.assertTrue(result['read_only'])
        self.assertEqual(result['total'], 1)
        session = result['sessions'][0]
        self.assertEqual(session['session_id'], 'session-one')
        self.assertEqual(session['title'], '织界宣传协作')
        self.assertEqual(session['message_count'], 2)
        self.assertNotIn('已整理课程定位', json.dumps(result, ensure_ascii=False))

    def test_workspace_filter_includes_descendants_but_not_sibling_prefix(self):
        self.transcript()
        self.transcript('nested', 'nested', self.workspace / '宣传计划')
        self.transcript('other', 'other', self.root / 'loom-os-other')
        ids = {s['session_id'] for s in self.list_sessions()['sessions']}
        self.assertEqual(ids, {'session-one', 'nested'})

    def test_lists_all_workspaces_only_when_explicitly_requested(self):
        self.transcript('other', 'other', self.root / 'another-project')
        self.assertEqual(self.list_sessions()['total'], 0)
        self.assertEqual(wb.list_local_sessions(self.config, None)['total'], 1)

    def test_sorts_by_record_timestamp_and_applies_limit_after_filter(self):
        self.transcript('older', 'older')
        records = [
            {'type': 'message', 'sessionId': 'newer', 'cwd': str(self.workspace),
             'role': 'user', 'timestamp': 6000, 'content': 'new'},
            {'type': 'ai-title', 'sessionId': 'newer', 'timestamp': 7000, 'aiTitle': '较新的宣传会话'},
        ]
        self.transcript('newer', 'newer', records=records)
        result = self.list_sessions(limit=1)
        self.assertEqual(result['sessions'][0]['session_id'], 'newer')
        self.assertEqual(result['total'], 2)
        self.assertTrue(result['has_more'])
        self.assertEqual(self.list_sessions(query='较新')['total'], 1)

    def test_history_returns_user_assistant_text_only_in_original_order(self):
        path = self.transcript()
        with path.open('a') as f:
            for record in [
                {'type': 'reasoning', 'text': 'private thought'},
                {'type': 'function_call_result', 'output': 'private tool result'},
                {'type': 'message', 'role': 'system', 'content': 'system instructions'},
                {'type': 'message', 'role': 'user', 'isMeta': True, 'content': 'injected reminder'},
                {'type': 'message', 'role': 'assistant', 'content': [{'type': 'image', 'data': 'image-payload'}]},
            ]:
                f.write(json.dumps(record) + '\n')
        result = self.history()
        self.assertEqual([m['role'] for m in result['messages']], ['user', 'assistant'])
        self.assertEqual([m['text'] for m in result['messages']], ['请整理织界宣传计划', '已整理课程定位'])
        self.assertEqual(result['total'], 2)
        self.assertNotIn('private thought', json.dumps(result))
        self.assertNotIn('private tool result', json.dumps(result))
        self.assertNotIn('injected reminder', json.dumps(result))

    def test_history_tail_and_role_filter(self):
        path = self.transcript()
        with path.open('a') as f:
            f.write(json.dumps({'type': 'message', 'sessionId': 'session-one', 'role': 'user',
                                'cwd': str(self.workspace), 'content': 'latest question'}) + '\n')
        result = self.history(limit=2)
        self.assertEqual([m['text'] for m in result['messages']], ['已整理课程定位', 'latest question'])
        self.assertTrue(result['has_more'])
        result = self.history(role='assistant', limit=2)
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['messages'][0]['text'], '已整理课程定位')

    def test_message_truncation_is_reported(self):
        self.transcript()
        result = self.history(max_chars=3)
        self.assertEqual(result['messages'][0]['text'], '请整理')
        self.assertTrue(result['messages'][0]['truncated'])

    def test_cumulative_text_budget_keeps_latest_messages_and_reports_more(self):
        records = [
            {'type': 'message', 'id': f'message-{i}', 'sessionId': 'session-one',
             'cwd': str(self.workspace), 'role': 'assistant', 'content': 'x' * 100000}
            for i in range(8)
        ]
        self.transcript(records=records)
        result = self.history(limit=1000, max_chars=100000)
        self.assertLessEqual(sum(len(m['text']) for m in result['messages']), 200000)
        self.assertEqual([m['id'] for m in result['messages']], ['message-6', 'message-7'])
        self.assertEqual(result['total'], 8)
        self.assertTrue(result['has_more'])

    def test_malformed_line_and_partial_tail_are_reported_not_silently_hidden(self):
        path = self.transcript()
        with path.open('a') as f:
            f.write('{bad-json}\n{"type":')
        result = self.history()
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['skipped_records'], 2)
        self.assertTrue(result['warnings'])

    def test_missing_store_is_not_reported_as_successful_empty_history(self):
        with self.assertRaises(wb.WorkBuddyError) as raised:
            wb.list_local_sessions(self.root / 'missing', self.workspace)
        self.assertEqual(raised.exception.code, 'local_store_not_found')

    def test_missing_session_has_explicit_error(self):
        with self.assertRaises(wb.WorkBuddyError) as raised:
            self.history()
        self.assertEqual(raised.exception.code, 'session_not_found')

    def test_path_traversal_session_id_is_rejected(self):
        for sid in ['../secret', '/etc/passwd', 'a/b', '*', '[abc]', '']:
            with self.subTest(sid=sid), self.assertRaises(wb.WorkBuddyError) as raised:
                self.history(sid)
            self.assertEqual(raised.exception.code, 'invalid_session_id')

    def test_other_workspace_history_is_not_returned(self):
        self.transcript(workspace=self.root / 'unrelated')
        with self.assertRaises(wb.WorkBuddyError) as raised:
            self.history()
        self.assertEqual(raised.exception.code, 'session_not_found')

    def test_duplicate_session_ids_require_workspace_disambiguation(self):
        self.transcript(project='one')
        self.transcript(project='two')
        with self.assertRaises(wb.WorkBuddyError) as raised:
            self.history()
        self.assertEqual(raised.exception.code, 'ambiguous_session')

    def test_foreign_session_records_are_excluded(self):
        path = self.transcript()
        with path.open('a') as f:
            f.write(json.dumps({'type': 'message', 'sessionId': 'foreign', 'role': 'assistant',
                                'cwd': str(self.workspace), 'content': 'wrong conversation'}) + '\n')
        self.assertEqual(self.history()['total'], 2)

    def test_symlinked_history_is_not_followed(self):
        path = self.transcript()
        alias = path.parent / 'symlink-session.jsonl'
        alias.symlink_to(path)
        with self.assertRaises(wb.WorkBuddyError):
            self.history('symlink-session')
        self.assertEqual(self.list_sessions()['total'], 1)

    def test_history_read_does_not_change_files(self):
        path = self.transcript()
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        self.history()
        self.list_sessions()
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
        self.assertEqual(set(path.parent.iterdir()), {path})

    def test_cli_exposes_both_commands_and_read_only_json(self):
        self.transcript()
        for args in [('sessions',), ('history', '--session-id', 'session-one')]:
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                data = json.loads(result.stdout)
                self.assertTrue(data['read_only'])
                self.assertEqual(data['source'], 'local')

    def test_cli_missing_session_uses_existing_error_envelope(self):
        result = self.cli('history', '--session-id', 'missing')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['error_code'], 'session_not_found')

    def test_cli_rejects_unbounded_or_invalid_limits(self):
        self.transcript()
        for args in [('sessions', '--limit', '0'), ('history', '--session-id', 'session-one', '--max-chars', '-1')]:
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
