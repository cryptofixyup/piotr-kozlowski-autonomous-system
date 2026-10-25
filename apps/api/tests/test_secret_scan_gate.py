import copy
import json

import pytest

from scripts.check_trufflehog import evaluate_report


@pytest.fixture
def evaluate():
    return evaluate_report


def finding(line=19):
    return {
        'SourceMetadata': {'Data': {'Git': {
            'commit': 'f0970a1d9a1d78bb90877e11385877246c9c78ee',
            'file': 'docker-compose.yml', 'line': line,
        }}},
        'DetectorName': 'Postgres',
        'Verified': False,
        'Raw': ''.join(['postgresql://', 'autonomous:', 'local-dev-only', '@postgres:5432']),
    }


def test_only_exact_historical_development_findings_are_accepted(evaluate):
    report = '\n'.join(json.dumps(finding(line)) for line in (19, 33))
    assert evaluate(report, 183) == (2, [])


@pytest.mark.parametrize('change', ['verified', 'commit', 'file', 'line', 'detector', 'raw'])
def test_new_or_verified_secret_findings_remain_blocking(evaluate, change):
    item = copy.deepcopy(finding())
    if change == 'verified':
        item['Verified'] = True
    elif change in ('commit', 'file', 'line'):
        item['SourceMetadata']['Data']['Git'][change] = 999 if change == 'line' else 'different'
    elif change == 'detector':
        item['DetectorName'] = 'Different'
    else:
        item['Raw'] += '-different'
    count, blockers = evaluate(json.dumps(item), 183)
    assert count == 0
    assert len(blockers) == 1
    assert item['Raw'] not in blockers[0]


@pytest.mark.parametrize('report,status', [('', 1), ('', 183), ('not json', 183), ('{}', 183)])
def test_scanner_failure_or_malformed_report_fails_closed(evaluate, report, status):
    with pytest.raises(ValueError):
        evaluate(report, status)


def test_clean_scan_passes(evaluate):
    assert evaluate('', 0) == (0, [])
