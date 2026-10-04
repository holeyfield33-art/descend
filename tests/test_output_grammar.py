import json

import pytest

from descend.dsl.decoding import allowed_output_tokens


class Tokenizer:
    eos_token_id = 9
    def get_vocab(self):
        return {"a": 1, "b": 2, "ab": 3, "c": 4, " a": 5, "": 6, "<end>": 9}
    def decode(self, identifiers, **kwargs):
        return {1: "a", 2: "b", 3: "ab", 4: "c", 5: " a", 6: "", 9: "<end>"}[identifiers[0]]


def test_output_grammar_uses_only_source_characters_and_eos():
    for operators in (["first"], ["unknown", "other"]):
        task = json.dumps({"string": "abba", "operators": operators})
        assert allowed_output_tokens(Tokenizer(), task) == [1, 2, 3, 9]
    with pytest.raises(ValueError):
        allowed_output_tokens(Tokenizer(), json.dumps({"string": "bad text", "operators": []}))
