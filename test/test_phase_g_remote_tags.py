"""Real Git integration tests for tag custody, using a temporary bare origin."""
import subprocess

import pytest

from tools import check_phase_g_custody as custody


def git(repo, *args):
    return subprocess.check_output(['git', *args], cwd=repo, text=True, stderr=subprocess.PIPE).strip()


@pytest.fixture
def repository(tmp_path):
    origin, repo = tmp_path / 'origin.git', tmp_path / 'repo'
    git(tmp_path, 'init', '--bare', str(origin))
    git(tmp_path, 'init', str(repo))
    git(repo, 'config', 'user.name', 'Custody test')
    git(repo, 'config', 'user.email', 'custody@example.invalid')
    docs = repo / 'docs/phase-G'
    docs.mkdir(parents=True)
    (docs / '00-test.md').write_text('Tag `phase-G2-example-prereg`.\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-m', 'fixture')
    git(repo, 'remote', 'add', 'origin', str(origin))
    return repo


def test_reference_missing_both_locally_and_remotely_is_not_ignored(repository):
    result = custody.check_remote_tags(repository)
    assert not result['pass']
    assert result['missing_local'] == result['missing_remote'] == ['phase-G2-example-prereg']


@pytest.mark.parametrize('annotated', [False, True])
def test_missing_remote_fails_then_push_passes(repository, annotated):
    args = ['tag', 'phase-G2-example-prereg']
    if annotated:
        args += ['-m', 'signed fixture']
    git(repository, *args)
    assert custody.check_remote_tags(repository)['missing_remote'] == ['phase-G2-example-prereg']
    git(repository, 'push', 'origin', '--tags')
    result = custody.check_remote_tags(repository)
    assert result['pass']
    assert result['referenced_tag_count'] == 1
    assert result['verified_object_ids']['phase-G2-example-prereg'] == git(repository, 'rev-parse', 'refs/tags/phase-G2-example-prereg')


def test_same_name_different_target_fails_even_when_tag_counts_match(repository):
    git(repository, 'tag', 'phase-G2-example-prereg')
    git(repository, 'push', 'origin', '--tags')
    git(repository, 'commit', '--allow-empty', '-m', 'another commit')
    git(repository, 'tag', '-f', 'phase-G2-example-prereg')
    result = custody.check_remote_tags(repository)
    assert not result['pass']
    assert result['local_tag_count'] == result['remote_tag_count'] == 1
    assert 'phase-G2-example-prereg' in result['mismatches']


def test_unavailable_origin_fails_closed(repository):
    git(repository, 'remote', 'set-url', 'origin', str(repository / 'missing.git'))
    result = custody.check_remote_tags(repository)
    assert result['pass'] is False and result['checked'] is False


def test_empty_document_scan_fails_closed(tmp_path):
    result = custody.check_remote_tags(tmp_path)
    assert result['pass'] is False and 'no Phase G documents' in result['error']


def test_reference_scan_deduplicates_and_preserves_source_documents(repository):
    (repository / 'docs/phase-G/01-test.md').write_text(
        '`phase-G2-example-prereg` twice: phase-G2-example-prereg. '
        'And phase-G-old-tag; folder docs/phase-G/ is not a tag.')
    refs = custody.referenced_phase_g_tags(repository)
    assert refs['phase-G2-example-prereg'] == ['docs/phase-G/00-test.md', 'docs/phase-G/01-test.md']
    assert refs['phase-G-old-tag'] == ['docs/phase-G/01-test.md']


def test_default_cli_fails_when_backup_passes_but_origin_fails(monkeypatch, capsys):
    import json
    monkeypatch.setattr('sys.argv', ['check_phase_g_custody'])
    monkeypatch.setattr(custody, 'evaluate', lambda deep=False: {
        'pass': True, 'phase_g_local_work_allowed': True,
        'campaign_execution_allowed': True, 'public_archival_claim_allowed': False})
    monkeypatch.setattr(custody, 'check_remote_tags', lambda: {'pass': False, 'checked': True})
    assert custody.main() == 1
    output = json.loads(capsys.readouterr().out)
    assert output['local_backup_pass'] is True
    assert output['campaign_execution_allowed'] is False


def test_tags_only_cli_does_not_depend_on_host_backup(monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', ['check_phase_g_custody', '--tags-only'])
    monkeypatch.setattr(custody, 'evaluate', lambda **kw: pytest.fail('must not read host backup'))
    monkeypatch.setattr(custody, 'check_remote_tags', lambda: {'pass': True, 'checked': True})
    assert custody.main() == 0


def test_local_only_cli_is_explicitly_offline(monkeypatch, capsys):
    import json
    monkeypatch.setattr('sys.argv', ['check_phase_g_custody', '--local-only'])
    monkeypatch.setattr(custody, 'evaluate', lambda deep=False: {'pass': True})
    monkeypatch.setattr(custody, 'check_remote_tags', lambda: pytest.fail('offline mode must not contact origin'))
    assert custody.main() == 0
    assert json.loads(capsys.readouterr().out)['remote_tags']['checked'] is False
