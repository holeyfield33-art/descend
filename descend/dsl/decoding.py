"""Input-only output grammar for operations that select/reorder/duplicate characters."""
import json


def allowed_output_tokens(tokenizer, task_input):
    command = json.loads(task_input)
    source = command["string"]
    if not isinstance(source, str) or not source or not source.isascii() or not source.isalnum():
        raise ValueError("Expected an ASCII alphanumeric source string")
    alphabet = set(source)
    # These tokenizer vocabulary pieces are literal ASCII and decode identically.
    # No hidden output, operator semantics or gold answer enters this calculation.
    allowed = [identifier for piece, identifier in tokenizer.get_vocab().items()
               if piece and all(character in alphabet for character in piece)
               and tokenizer.decode([identifier], skip_special_tokens=False) == piece]
    allowed.append(tokenizer.eos_token_id)
    return sorted(set(allowed))
