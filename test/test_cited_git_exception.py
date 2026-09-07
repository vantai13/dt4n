import hashlib

from tools.check_cited_git_exception import TARGET, matches_decision


def test_exception_accepts_only_exact_cited_bytes_and_explicit_decision():
    content = b'fixed measurement'
    digest = hashlib.sha256(content).hexdigest()
    cert = {'evidence_sha256': {TARGET: digest}}
    decision = {'classification': 'CITED_RAW', 'git_distribution_allowed': True,
                'path': TARGET, 'bytes': len(content), 'sha256': digest}
    assert matches_decision(TARGET, content, decision, cert)
    assert not matches_decision('unrelated.npz', content, decision, cert)
    assert not matches_decision(TARGET, b'changed measurement', decision, cert)
    assert not matches_decision(TARGET, content, {**decision, 'git_distribution_allowed': False}, cert)
    assert not matches_decision(TARGET, content, {**decision, 'sha256': '0' * 64}, cert)
    assert not matches_decision(TARGET, content, decision, {})
