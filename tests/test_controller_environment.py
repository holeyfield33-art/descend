import pytest

from descend.controller.environment import (
    EnvironmentSyntaxError, load_controller_environment, parse_environment,
)


def test_literal_values_and_comment_handling():
    values = parse_environment('\ufeff# ignored\nexport NEBIUS_API_KEY="literal$KEY#part" # note\nAGENT_MODEL_ID=model # note\n')
    assert values == {"NEBIUS_API_KEY": "literal$KEY#part", "AGENT_MODEL_ID": "model"}


@pytest.mark.parametrize("text", [
    '$env:NEBIUS_API_KEY="secret"', 'NEBIUS_API_KEY="secret',
    'NEBIUS_API_KEY="secret" trailing', 'PYTHONPATH=secret',
    'NEBIUS_API_KEY=secret\nNEBIUS_API_KEY=other',
])
def test_errors_do_not_echo_values(text):
    with pytest.raises(EnvironmentSyntaxError) as failure:
        parse_environment(text)
    assert "secret" not in str(failure.value)


def test_load_is_atomic_and_preserves_environment(tmp_path):
    path = tmp_path / ".env"
    env = {"NEBIUS_API_KEY": "existing"}
    path.write_text("NEBIUS_API_KEY=file\nAGENT_MODEL_ID=model\n", encoding="utf-8-sig")
    assert load_controller_environment(path, environ=env) == 1
    assert env == {"NEBIUS_API_KEY": "existing", "AGENT_MODEL_ID": "model"}
    path.write_text("NEBIUS_API_KEY=file\nnot an assignment", encoding="utf-8")
    untouched = {}
    with pytest.raises(EnvironmentSyntaxError):
        load_controller_environment(path, environ=untouched)
    assert untouched == {}
