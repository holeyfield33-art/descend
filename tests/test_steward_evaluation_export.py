"""Public export must reject private identities/secrets and escape model text."""
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.export_steward_evaluation import export


def fixture(tmp_path):
    source=tmp_path/'source'
    source.mkdir()
    for name in ('summary.json','Super-scores.json','Nano-scores.json','Super.json','Nano.json','variance.json','act-metrics.json'):
        shutil.copyfile(Path('docs/evidence/steward-live-20261006')/name,source/name)
    return source


def test_model_html_is_escaped_and_public_manifest_verified(tmp_path):
    source=fixture(tmp_path)
    path=source/'Nano-scores.json'
    data=json.loads(path.read_text())
    data['false_positives'][0]['finding']['reason']='</pre><script>alert(1)</script>'
    path.write_text(json.dumps(data))
    target=tmp_path/'out'
    export(source,target)
    page=(target/'public/index.html').read_text()
    assert '<script>' not in page and '&lt;script&gt;' in page
    manifest=json.loads((target/'public/manifest.json').read_text())
    assert all(hashlib.sha256((target/'public'/name).read_bytes()).hexdigest()==digest for name,digest in manifest['files'].items())
    assert (target/'public/LICENSE').read_bytes()==Path('LICENSE').read_bytes()


@pytest.mark.parametrize('attack',['secret','unowned'])
def test_export_refuses_before_writing_public_files(tmp_path,attack):
    source=fixture(tmp_path)
    path=source/'Nano-scores.json'
    data=json.loads(path.read_text())
    if attack=='secret':
        data['false_positives'][0]['finding']['reason']='sk-'+'x'*30
    else:
        data['false_positives'][0]['case']='private-repo-case'
    path.write_text(json.dumps(data))
    target=tmp_path/'out'
    with pytest.raises(ValueError):
        export(source,target)
    assert not target.exists()
