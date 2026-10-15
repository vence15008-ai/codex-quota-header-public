import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from account_reader import AccountReader, find_codex


class AccountReaderTests(unittest.TestCase):
    def test_explicit_native_executable_and_no_cmd_wrapper(self):
        with tempfile.TemporaryDirectory() as folder:
            native = Path(folder) / 'codex.exe'
            native.touch()
            with patch.dict(os.environ, {'CODEX_QUOTA_CODEX': str(native)}):
                self.assertEqual(find_codex(), str(native.resolve()))
            with patch.dict(os.environ, {'CODEX_QUOTA_CODEX': str(native.with_suffix('.cmd'))}):
                with self.assertRaises(RuntimeError):
                    find_codex()

    def test_correlates_replies_and_ignores_notifications_or_garbage(self):
        reader = AccountReader()
        for line in ('invalid', '[]', '{"method":"notice"}', '{"id":2,"result":{}}',
                     '{"id":3,"result":{"rateLimits":{}}}'):
            reader.lines.put(line)
        self.assertEqual(reader._wait_for(3), {'rateLimits': {}})

    def test_errors_do_not_expose_arbitrary_server_text(self):
        reader = AccountReader()
        reader.lines.put(json.dumps({'id': 1, 'error': {'code': 401, 'message': 'SECRET'}}))
        with self.assertRaisesRegex(RuntimeError, 'code 401') as caught:
            reader._wait_for(1)
        self.assertNotIn('SECRET', str(caught.exception))

    def test_invalid_result(self):
        reader = AccountReader()
        reader.lines.put('{"id":1,"result":null}')
        with self.assertRaises(RuntimeError):
            reader._wait_for(1)

    def test_timeout(self):
        with self.assertRaises(TimeoutError):
            AccountReader()._wait_for(1, timeout=0.01)

    def test_reconnect_once_and_close_failed_server(self):
        reader = AccountReader()
        with patch.object(reader, '_start') as start, patch.object(reader, '_send') as send, \
                patch.object(reader, '_wait_for', side_effect=[RuntimeError('disconnected'), {'ok': True}]), \
                patch.object(reader, 'close') as close:
            self.assertEqual(reader.read_limits(), {'ok': True})
        self.assertEqual(start.call_count, 2)
        self.assertEqual(close.call_count, 1)
        self.assertEqual(send.call_args.args[0]['method'], 'account/rateLimits/read')

    def test_initialize_then_read_only_quota_protocol(self):
        process = MagicMock()
        process.poll.return_value = None
        process.stdin = io.StringIO()
        process.stdout = io.StringIO('{"id":1,"result":{}}\n{"id":2,"result":{"rateLimits":{}}}\n')
        with patch('account_reader.find_codex', return_value='codex.exe'), \
                patch('account_reader.subprocess.Popen', return_value=process) as popen:
            reader = AccountReader()
            try:
                self.assertEqual(reader.read_limits(), {'rateLimits': {}})
                messages = [json.loads(line) for line in process.stdin.getvalue().splitlines()]
                self.assertEqual([m['method'] for m in messages],
                                 ['initialize', 'initialized', 'account/rateLimits/read'])
                self.assertNotIn('shell', popen.call_args.kwargs)
                if os.name == 'nt':
                    self.assertEqual(popen.call_args.kwargs['creationflags'], subprocess.CREATE_NO_WINDOW)
            finally:
                reader.close()


if __name__ == '__main__':
    unittest.main()
