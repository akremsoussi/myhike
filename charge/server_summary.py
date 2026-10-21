"""Summarize server samples on the same UTC interval as the JMeter plateau."""
import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import re
from statistics import mean


def byte_count(value):
    number, unit = re.fullmatch(r'([\d.]+)\s*([A-Za-z]+)', value.strip()).groups()
    factors = {'B': 1, 'kB': 1000, 'KB': 1000, 'MB': 1000**2, 'GB': 1000**3,
               'KiB': 1024, 'MiB': 1024**2, 'GiB': 1024**3}
    return float(number) * factors[unit]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('samples')
    parser.add_argument('statistics')
    parser.add_argument('output')
    args = parser.parse_args()
    with Path(args.statistics).open(encoding='utf-8-sig', newline='') as stream:
        stats = next(csv.DictReader(stream))
    start, end = int(stats['measurement_start_ms']), int(stats['measurement_end_ms'])
    with Path(args.samples).open(encoding='utf-8-sig') as stream:
        samples = [json.loads(line) for line in stream if line.strip()]
    samples = [s for s in samples if start <= datetime.fromisoformat(s['timestamp_utc'].replace('Z', '+00:00')).timestamp()*1000 < end]
    if not samples:
        raise ValueError('No server samples in the measurement window')
    bad = sum(s['docker_stats_exit'] != 0 or s['mysql_status_exit'] != 0 for s in samples)
    services = {}
    connections, running, reads, writes = [], [], [], []
    java_cpu = [s['java_cpu_percent_host'] for s in samples if s['java_cpu_percent_host'] is not None]
    for sample in samples:
        for text in sample['docker_stats']:
            try:
                item = json.loads(text)
                group = services.setdefault(item['Name'], {'cpu': [], 'memory': [], 'read': [], 'write': []})
                group['cpu'].append(float(item['CPUPerc'].rstrip('%')))
                group['memory'].append(byte_count(item['MemUsage'].split('/')[0]))
                disk_read, disk_write = item['BlockIO'].split('/')
                group['read'].append(byte_count(disk_read))
                group['write'].append(byte_count(disk_write))
            except (ValueError, KeyError, AttributeError):
                bad += 1
        status = {}
        for line in sample['mysql_status']:
            pieces = line.split('\t')
            if len(pieces) == 2 and pieces[1].isdigit():
                status[pieces[0]] = int(pieces[1])
        if 'Threads_connected' in status:
            connections.append(status['Threads_connected'])
            running.append(status['Threads_running'])
            reads.append(status['Innodb_data_read'])
            writes.append(status['Innodb_data_written'])
    if bad or not connections or len(services) != 3:
        raise ValueError(f'Incomplete server collection: {bad} errors, {len(services)} services')
    result = {
        'users': int(stats['users']), 'samples': len(samples), 'collection_errors': bad,
        'measurement_start_ms': start, 'measurement_end_ms': end,
        'java_cpu_percent_host_mean': mean(java_cpu) if java_cpu else None,
        'java_cpu_percent_host_max': max(java_cpu) if java_cpu else None,
        'java_working_set_bytes_max': max(s['java_working_set_bytes'] or 0 for s in samples),
        'mysql_connections_mean': mean(connections), 'mysql_connections_max': max(connections),
        'mysql_running_max': max(running),
        'innodb_read_bytes_delta': max(reads) - min(reads),
        'innodb_written_bytes_delta': max(writes) - min(writes),
        'services': {name: {
            'cpu_percent_mean': mean(g['cpu']), 'cpu_percent_max': max(g['cpu']),
            'memory_bytes_mean': mean(g['memory']), 'memory_bytes_max': max(g['memory']),
            'block_read_bytes_delta': max(g['read']) - min(g['read']),
            'block_written_bytes_delta': max(g['write']) - min(g['write']),
        } for name, g in services.items()},
    }
    Path(args.output).write_text(json.dumps(result, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
