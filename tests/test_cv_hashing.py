"""AST-normalized pipeline hashing (cv_config.normalized_source).

Cosmetic edits — comments, docstrings, blank lines, reformatting — must NOT change the
digest, so they don't force a spurious PIPELINE_VERSION bump. Code / literal-value
changes MUST change it, so real pipeline changes are still caught by cv_assign's gate.
"""
import hashlib
from pathlib import Path

import cv_config


def _digest(path) -> str:
    return hashlib.sha256(cv_config.normalized_source(path).encode("utf-8")).hexdigest()


def _write(tmp_path, name, src) -> Path:
    p = tmp_path / name
    p.write_text(src, encoding="utf-8")
    return p


BASE = 'X = 5\n\n\ndef f():\n    """doc."""\n    return X + 1\n'


def test_comments_and_docstrings_ignored(tmp_path):
    base = _digest(_write(tmp_path, "a.py", BASE))
    cosmetic = _digest(_write(
        tmp_path, "b.py",
        '# leading comment\nX = 5\ndef f():\n    """a totally different docstring."""\n'
        '    return X + 1  # trailing comment\n',
    ))
    assert cosmetic == base


def test_reformatting_ignored(tmp_path):
    base = _digest(_write(tmp_path, "a.py", BASE))
    reflowed = _digest(_write(tmp_path, "b.py", "X=5\ndef f():\n    return X+1\n"))
    assert reflowed == base


def test_value_change_detected(tmp_path):
    base = _digest(_write(tmp_path, "a.py", BASE))
    changed = _digest(_write(tmp_path, "b.py", "X = 6\ndef f():\n    return X + 1\n"))
    assert changed != base


def test_appending_a_comment_to_cv_config_is_a_noop(tmp_path):
    """The exact landmine this fixes: a trailing comment on cv_config.py."""
    original = Path(cv_config.__file__).read_text(encoding="utf-8")
    with_comment = _write(tmp_path, "cv_config_copy.py",
                          original + "\n# an extra trailing comment\n")
    assert cv_config.normalized_source(with_comment) == cv_config.normalized_source(cv_config.__file__)
