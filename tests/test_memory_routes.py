from __future__ import annotations

from src.memory.routes import _merge_user_tags


def test_merge_user_tags() -> None:
    tags = _merge_user_tags(7, ['vin:123'])
    assert 'user:7' in tags
    assert 'vin:123' in tags

    tags2 = _merge_user_tags(7, ['user:7', 'kind:session'])
    assert tags2.count('user:7') == 1
