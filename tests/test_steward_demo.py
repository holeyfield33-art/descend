"""Owned fixture end-to-end demo exercises the actual isolated worker."""
import hashlib
import json
import sys

import pytest

from descend.sandbox.hard_isolation import isolation_available
from scripts.demo_steward import run


@pytest.mark.skipif(sys.platform != 'linux' or not isolation_available()['available'], reason='Demo execution requires Linux namespace worker')
def test_demo_restart_and_export_boundary(tmp_path):
    output = tmp_path/'demo'
    result = run(output)
    assert result['complete']
    assert result['provider_calls'] == 0
    assert result['checkout_unchanged']
    assert result['idle_mock_calls'] == result['restart_mock_calls'] == 0
    assert result['repeated_action_claim'] is False
    manifest = json.loads((output/'public/manifest.json').read_text())
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((output/'public'/name).read_bytes()).hexdigest() == digest
    page = (output/'public/index.html').read_text()
    assert '<script' not in page and '<form' not in page
    assert 'MOCK' in page
    with pytest.raises(FileExistsError):
        run(output)
