import http.client
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from rtl_json_pipeline.api import request_json

class RecoveryTests(unittest.TestCase):
    def test_interrupted_response_retries(self):
        invoke=Mock(side_effect=[http.client.IncompleteRead(b''),'{}'])
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(request_json('s','u',d,invoke=invoke,sleep=lambda _:None),'{}')
            self.assertEqual(invoke.call_count,2)
    def test_auth_not_retried(self):
        invoke=Mock(side_effect=RuntimeError('DeepSeek HTTP 401: invalid API key'))
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):request_json('s','u',d,invoke=invoke,sleep=lambda _:None)
        self.assertEqual(invoke.call_count,1)
    def test_retry_is_bounded(self):
        invoke=Mock(side_effect=http.client.IncompleteRead(b''))
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(http.client.IncompleteRead):request_json('s','u',d,invoke=invoke,sleep=lambda _:None)
        self.assertEqual(invoke.call_count,3)
    def test_length_fallback_recorded(self):
        invoke=Mock(side_effect=[RuntimeError("Incomplete completion: 'length'; inspect API logs."),'{}'])
        with tempfile.TemporaryDirectory() as d:
            request_json('s','u',d,invoke=invoke,sleep=lambda _:None)
            logs=json.loads((Path(d)/'request_attempts.json').read_text())
            self.assertEqual(logs[-1]['reasoning_effort'],'none')

if __name__=='__main__':unittest.main()
