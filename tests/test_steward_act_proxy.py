import hashlib
import json
from types import SimpleNamespace

import pytest

from descend.controller.spend import SpendLedger
from descend.steward.act import ActStore
from descend.steward.act_proxy import generate_proposal

DIFF = '--- a/app.py\n+++ b/app.py\n@@ -0,0 +1,2 @@\n+def solve(values):\n+    return sum(values[:-1])\n'
SOURCE = 'def solve(values):\n    return sum(values[:-1])\n'
FINDING = dict(path='app.py', line=2, evidence='return sum(values[:-1])', severity='low', reason='canned', verification='test')
RAW = json.dumps(dict(path='app.py', test_source='from app import solve\ndef test_reproducer():\n    assert solve([1,2]) == 3\n', replacement_source='def solve(values):\n    return sum(values)\n', expected_failure='AssertionError'))


class Client:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail
        self.chat = SimpleNamespace(completions=self)

    def with_options(self, **options):
        assert options == {'max_retries': 0, 'timeout': 60}
        return self

    def create(self, **body):
        self.calls.append(body)
        if self.fail:
            raise RuntimeError('simulated ambiguous call')
        return SimpleNamespace(model_dump=lambda **_: dict(id='mock-provider-id', usage=dict(prompt_tokens=10, completion_tokens=20), choices=[dict(message=dict(content=RAW))]))


def invoke(tmp_path, client, **kwargs):
    return generate_proposal(dict(repo='owned', sha='a'*40, status='ready', diff=DIFF, paths=['app.py'], diff_sha256=hashlib.sha256(DIFF.encode()).hexdigest()),
                             FINDING, SOURCE, store=ActStore(tmp_path/'acts.sqlite'), ledger=SpendLedger(tmp_path/'mock-spend.sqlite'),
                             client=client, finding_index=0, **kwargs)


def test_single_call_reservation_and_replay(tmp_path):
    client = Client()
    result = invoke(tmp_path, client)
    assert result['classification'] == 'proposal_ready'
    assert len(client.calls) == 1
    assert client.calls[0]['max_tokens'] == 2000
    with pytest.raises(RuntimeError, match='claimed'):
        invoke(tmp_path, client)
    assert len(client.calls) == 1
    assert SpendLedger(tmp_path/'mock-spend.sqlite').summary()['unresolved_calls'] == 0


def test_zero_cap_and_ambiguous_failure_no_retry(tmp_path):
    client = Client(fail=True)
    with pytest.raises(RuntimeError, match='budget'):
        invoke(tmp_path, client, commit_cap=0)
    assert client.calls == []
    with pytest.raises(RuntimeError, match='no automatic retry'):
        invoke(tmp_path, client)
    with pytest.raises(RuntimeError, match='claimed'):
        invoke(tmp_path, client)
    assert len(client.calls) == 1
    assert SpendLedger(tmp_path/'mock-spend.sqlite').summary()['unresolved_calls'] == 1
