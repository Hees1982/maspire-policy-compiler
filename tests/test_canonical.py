from app.canonical import canonical_json, policy_checksum


def test_checksum_is_stable_across_key_order():
    left = {"version": "1", "policy_id": "p"}
    right = {"policy_id": "p", "version": "1"}
    assert canonical_json(left) == canonical_json(right)
    assert policy_checksum(left) == policy_checksum(right)


def test_checksum_changes_with_policy():
    assert policy_checksum({"version": "1"}) != policy_checksum({"version": "2"})

