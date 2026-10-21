import sys
import csv
import math

if len(sys.argv) < 2:
    print("Usage: python analyser_palier.py <fichier.csv>")
    sys.exit(1)

csv_path = sys.argv[1]

rows = []
with open(csv_path, mode='r', encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for r in reader:
        # Ignorer les lignes incomplètes ou tronquées
        if not r.get('success') or not r.get('elapsed') or not r.get('timeStamp'):
            continue
        try:
            int(r['elapsed'])
            int(r['timeStamp'])
            rows.append(r)
        except ValueError:
            continue

if not rows:
    print("Erreur: Le fichier CSV ne contient aucune ligne valide.")
    sys.exit(1)

total_samples = len(rows)
success_count = sum(1 for r in rows if r['success'].strip().lower() == 'true')
error_count = total_samples - success_count
error_rate = (error_count / total_samples) * 100

timestamps = [int(r['timeStamp']) for r in rows]
elapsed = [int(r['elapsed']) for r in rows]

start_time = min(timestamps)
end_time = max(t + e for t, e in zip(timestamps, elapsed))
duration_sec = (end_time - start_time) / 1000.0
throughput = total_samples / duration_sec if duration_sec > 0 else 0

def percentile(data, p):
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return d0 + d1

p50 = percentile(elapsed, 50)
p90 = percentile(elapsed, 90)
p95 = percentile(elapsed, 95)
p99 = percentile(elapsed, 99)
avg_lat = sum(elapsed) / len(elapsed)
min_lat = min(elapsed)
max_lat = max(elapsed)

print("=" * 60)
print(f"ANALYSE DE {csv_path}")
print("=" * 60)
print(f"Nombre total d'échantillons  : {total_samples}")
print(f"Durée totale de la mesure    : {duration_sec:.2f} s")
print(f"Débit global                 : {throughput:.2f} req/s")
print(f"Taux d'erreur global         : {error_rate:.2f} % ({error_count}/{total_samples})")
print("-" * 60)
print("DISTRIBUTION DE LA LATENCE (ms) :")
print(f"  Min                        : {min_lat} ms")
print(f"  Moyenne                    : {avg_lat:.1f} ms")
print(f"  Médiane (50e centile)      : {p50:.1f} ms")
print(f"  90e centile                : {p90:.1f} ms")
print(f"  95e centile (Référence)    : {p95:.1f} ms")
print(f"  99e centile                : {p99:.1f} ms")
print(f"  Max                        : {max_lat} ms")
print("-" * 60)
print("PAR TYPE DE REQUÊTE :")
labels = sorted(list(set(r['label'] for r in rows)))
for lbl in labels:
    sub = [r for r in rows if r['label'] == lbl]
    sub_total = len(sub)
    sub_err = sum(1 for r in sub if r['success'].strip().lower() != 'true')
    sub_el = [int(r['elapsed']) for r in sub]
    sub_p50 = percentile(sub_el, 50)
    sub_p95 = percentile(sub_el, 95)
    print(f"  * {lbl}:")
    print(f"      Nombre: {sub_total} | Erreurs: {sub_err} ({(sub_err/sub_total)*100:.1f}%) | Médiane: {sub_p50:.1f} ms | 95e: {sub_p95:.1f} ms")
print("=" * 60)
