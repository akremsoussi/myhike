"""Compute repetition spreads directly from the measured per-level statistics."""
import argparse
from collections import defaultdict
import csv
from pathlib import Path
from statistics import mean


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('session')
    args = parser.parse_args()
    session = Path(args.session)
    groups = defaultdict(list)
    for file in session.glob('*-statistiques.csv'):
        with file.open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.DictReader(stream):
                if row['label'] == 'Total':
                    groups[int(row['users'])].append(row)
    if not groups:
        raise ValueError('No measured statistics')
    result = []
    for users, rows in sorted(groups.items()):
        record = {'users': users, 'repetitions': len(rows)}
        for source, target in [('throughput_rps', 'throughput_spread_pct'), ('p95_ms', 'p95_spread_pct')]:
            values = [float(r[source]) for r in rows]
            record[target] = 100*(max(values)-min(values))/max(mean(values), 0.0001)
        result.append(record)
    with (session/'repetabilite.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=result[0])
        writer.writeheader()
        writer.writerows(result)


if __name__ == '__main__':
    main()
