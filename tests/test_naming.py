from wktr.naming import normalize_branch_name, branch_to_dirname
from pathlib import Path

def test_normalize_branch_name():
    assert normalize_branch_name("feature/foo") == "feature-foo"
    assert normalize_branch_name("bugfix\\bar") == "bugfix-bar"
    assert normalize_branch_name("a:b*c?d\"e<f>g|h") == "a-b-c-d-e-f-g-h"
    assert normalize_branch_name("foo//bar") == "foo-bar"
    assert normalize_branch_name("-foo-") == "foo"
    assert normalize_branch_name("---") == ""

def test_branch_to_dirname(tmp_path):
    assert branch_to_dirname("feature/foo", tmp_path) == "feature-foo"
    
    # Collision
    (tmp_path / "feature-foo").mkdir()
    existing = {"feature-foo": "other-branch"}
    
    dirname = branch_to_dirname("feature/foo", tmp_path, existing)
    assert dirname.startswith("feature-foo--")
    assert len(dirname) == 11 + 2 + 7
    
    # Same branch
    existing = {"feature-foo": "feature/foo"}
    assert branch_to_dirname("feature/foo", tmp_path, existing) == "feature-foo"
