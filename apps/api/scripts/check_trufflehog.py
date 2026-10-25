"""Fail closed on scanner errors or any finding outside two reviewed dev fixtures."""
import hashlib
import json
from pathlib import Path
import sys


# Removed local-only Compose credentials, verified at this exact historical commit.
# No detector, file, or credential value is globally excluded.
DEV_COMMIT = 'f0970a1d9a1d78bb90877e11385877246c9c78ee'
DEV_HASH = 'ea0854ff6be115820a85977ebf9785f64043ea2ced129c6f20773fbd71dc51d5'


def evaluate_report(report: str, scanner_status: int) -> tuple[int, list[str]]:
    if scanner_status not in (0, 183):
        raise ValueError('TruffleHog did not complete successfully')
    try:
        records = [json.loads(line) for line in report.splitlines() if line.strip()]
    except json.JSONDecodeError as exc:
        raise ValueError('Malformed TruffleHog report') from exc
    if bool(records) != (scanner_status == 183):
        raise ValueError('TruffleHog status and report disagree')

    accepted = 0
    blockers = []
    for item in records:
        try:
            git = item['SourceMetadata']['Data']['Git']
            location = (git['commit'], git['file'], git['line'])
            detector = item['DetectorName']
            verified = item['Verified']
            raw_hash = hashlib.sha256(item['Raw'].encode('utf-8')).hexdigest()
            if not isinstance(verified, bool):
                raise TypeError('Verified must be a boolean')
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError('Malformed TruffleHog finding') from exc
        known = (
            verified is False
            and detector == 'Postgres'
            and location[0] == DEV_COMMIT
            and location[1] == 'docker-compose.yml'
            and location[2] in (19, 33)
            and raw_hash == DEV_HASH
        )
        if known:
            accepted += 1
        else:
            # Do not expose raw credentials in CI logs or exception messages.
            blockers.append(json.dumps({'detector': detector, 'location': location}))
    return accepted, blockers


def main() -> int:
    try:
        accepted, blockers = evaluate_report(
            Path(sys.argv[1]).read_text(encoding='utf-8'), int(sys.argv[2]),
        )
    except (ValueError, OSError, IndexError):
        print('TruffleHog scan or report validation failed')
        return 2
    print(f'TruffleHog: {accepted} exact historical dev findings, {len(blockers)} blocking findings')
    for blocker in blockers:
        print(blocker)
    return 1 if blockers else 0


if __name__ == '__main__':
    sys.exit(main())
