"""Keep raw JMeter data; extract the steady window and comparable statistics."""
import argparse
from array import array
import csv
import gzip
import json
import math
import shutil
from pathlib import Path


def percentile(values, percent):
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def summarize(raw, output, ramp, plateau, users):
    with Path(raw).open(encoding="utf-8-sig", newline="") as stream:
        markers = [row for row in csv.DictReader(stream) if row['label'] == '__measurement_origin']
    if len(markers) != 1:
        raise ValueError("Exactly one setup timestamp marker is required")
    origin = int(markers[0]["timeStamp"]) + int(markers[0]["elapsed"])
    # One additional second after ramp-up; total runtime has two seconds of margin.
    start = origin + (ramp + 1) * 1000
    end = start + plateau * 1000
    groups = {}
    with Path(raw).open(encoding='utf-8-sig', newline='') as source, Path(output).open('w', encoding='utf-8', newline='') as target:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(target, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            if not start <= int(row['timeStamp']) < end:
                continue
            writer.writerow(row)
            for label in ('Total', row['label']):
                group = groups.setdefault(label, {'elapsed': array('d'), 'errors': 0, 'threads': 0})
                group['elapsed'].append(float(row['elapsed']))
                group['errors'] += row['success'].lower() != 'true'
                group['threads'] = max(group['threads'], int(row.get('allThreads', 0)))
    if not groups:
        raise ValueError('No samples in the steady measurement window')
    labels = ['Total'] + sorted(label for label in groups if label != 'Total')
    statistics = []
    for label in labels:
        elapsed = groups[label]['elapsed']
        errors = groups[label]['errors']
        statistics.append({
            "users": users, "label": label, "samples": len(elapsed),
            "errors": errors, "error_pct": round(100 * errors / len(elapsed), 4),
            "mean_ms": round(sum(elapsed) / len(elapsed), 3),
            "median_ms": round(percentile(elapsed, 50), 3),
            "p90_ms": round(percentile(elapsed, 90), 3),
            "p95_ms": round(percentile(elapsed, 95), 3),
            "p99_ms": round(percentile(elapsed, 99), 3),
            "throughput_rps": round(len(elapsed) / plateau, 4),
            "max_active_threads": groups[label]['threads'],
            "measurement_start_ms": start, "measurement_end_ms": end,
        })
    return statistics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("steady")
    parser.add_argument("--ramp", type=int, required=True)
    parser.add_argument("--plateau", type=int, required=True)
    parser.add_argument("--users", type=int, required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()
    result = summarize(args.raw, args.steady, args.ramp, args.plateau, args.users)
    with Path(args.summary).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=result[0])
        writer.writeheader()
        writer.writerows(result)
    print(json.dumps(result[0]))
    if Path(args.raw).name.startswith('etalonnage-'):
        with Path(args.raw).open('rb') as source, gzip.open(args.raw + '.gz', 'wb') as target:
            shutil.copyfileobj(source, target)


if __name__ == "__main__":
    main()
