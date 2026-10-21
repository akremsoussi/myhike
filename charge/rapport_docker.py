"""Write a measured Docker report; leave the VM comparison explicitly pending."""
import argparse
import csv
import json
from pathlib import Path


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('session')
    parser.add_argument('--calibration')
    args = parser.parse_args()
    session = Path(args.session)
    config = json.loads((session/'configuration.json').read_text(encoding='utf-8-sig'))
    if config['completion'] != 'complete':
        raise ValueError('Campaign is not complete')
    lines = [
        '# Campagne Docker : résultats mesurés', '',
        f"Début UTC : {config['started_utc']}. Commit de référence : `{config['git_commit']}`.",
        'Les empreintes des plans, comptes et fichiers SQL sont conservées dans `configuration.json`.', '',
        '## Protocole', '',
        'Injecteur JMeter 5.6.3 en CLI sur Windows, hors des conteneurs. VMs arrêtées.',
        f"Paliers : {', '.join(map(str, config['users']))}. Répétitions : {config['repetitions']}.",
        f"Montée : {config['ramp_seconds']} s ; fenêtre mesurée : {config['steady_seconds']} s, hors montée.",
        'Une seconde de stabilisation supplémentaire est exclue. Les requêtes sont sélectionnées',
        'par leur instant de départ ; leur durée entière est conservée, même en cas de timeout.',
        'Base sauvegardée puis réinitialisée avant chaque série. Fichiers photo conservés.',
        'Scénario : connexion avec compte CSV, cookie de session, consultation des refuges.',
        'Temporisation : 500 à 1 000 ms avant chaque requête. Connexions TCP réutilisées.',
        'Contrôles positifs et négatifs exécutés avant chaque série.', '',
        '## Mesures applicatives (plateau uniquement)', '',
        '| Utilisateurs | Série | Requêtes | Erreurs (%) | Débit total (req/s) | Débit réussi (req/s) | Médiane (ms) | p90 (ms) | p95 (ms) | p99 (ms) |',
        '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|',
    ]
    totals = []
    for statistics in sorted(session.glob('*-statistiques.csv')):
        row = next(r for r in read_csv(statistics) if r['label'] == 'Total')
        repetition = statistics.name.split('-r')[1].split('-')[0]
        totals.append((int(row['users']), int(repetition), row, statistics))
    for users, repetition, row, _ in sorted(totals):
        successful = (int(row['samples']) - int(row['errors'])) / config['steady_seconds']
        lines.append(f"| {users} | {repetition} | {row['samples']} | {float(row['error_pct']):.2f} | {float(row['throughput_rps']):.2f} | {successful:.2f} | {row['median_ms']} | {row['p90_ms']} | {row['p95_ms']} | {row['p99_ms']} |")
    lines += ['', 'Le débit total inclut les échecs. Un p95 proche de 30 000 ms avec un fort taux',
              "d'erreur indique surtout le timeout client de 30 s, et non la latence des réponses réussies.", '',
              '## Répétabilité', '',
              '| Utilisateurs | Écart de débit (%) | Écart de p95 (%) |', '|---:|---:|---:|']
    repeatability = read_csv(session/'repetabilite.csv') if (session/'repetabilite.csv').exists() else []
    for row in repeatability:
        lines.append(f"| {row['users']} | {float(row['throughput_spread_pct']):.2f} | {float(row['p95_spread_pct']):.2f} |")
    lines += ['', 'Écart = (maximum - minimum) / moyenne des répétitions. Les écarts supérieurs à',
              '10 % doivent être explicités ou contrôlés par une nouvelle campagne dans des conditions stables.', '',
              '## Ressources et goulot observé', '',
              '| Utilisateurs | Série | CPU backend moyen (% Docker) | Mémoire backend max (MiB) | Connexions MySQL max | CPU injecteur moyen (% hôte) |',
              '|---:|---:|---:|---:|---:|---:|']
    for users, repetition, _, statistics in sorted(totals):
        stem = statistics.name.removesuffix('-statistiques.csv')
        metrics = json.loads((session/(stem+'-serveur-synthese.json')).read_text(encoding='utf-8-sig'))
        backend = metrics['services']['refuges-backend-1']
        lines.append(f"| {users} | {repetition} | {backend['cpu_percent_mean']:.1f} | {backend['memory_bytes_max']/1024**2:.1f} | {metrics['mysql_connections_max']} | {metrics['java_cpu_percent_host_mean']:.2f} |")
    lines += ['', 'Dans Docker, 100 % CPU correspond à un cœur logique ; plusieurs centaines de',
              'pour cent ne sont donc pas une erreur. Les connexions MySQL incluent celle du relevé.',
              'Le détail des entrées-sorties et les relevés horodatés sont conservés dans les fichiers serveur.', '']
    evidence = any('QueuePool limit of size 5 overflow 10 reached' in file.read_text(encoding='utf-8-sig', errors='replace')
                   for file in session.glob('backend-*.txt'))
    if evidence:
        lines += ['Les journaux conservés montrent une saturation du pool SQLAlchemy :',
                  '`QueuePool limit of size 5 overflow 10 reached`, soit 15 connexions, avec un délai de 30 s.',
                  'Cette observation explique les erreurs de pool. Elle ne prouve pas une saturation du moteur MySQL.',
                  "L'influence du pool, des threads de traitement et du coût Argon2 devra être isolée dans une expérience séparée.", '']
    else:
        lines += ["Consulter les journaux du backend avant de conclure sur l'origine d'une saturation.", '']
    lines += ["Aucun réglage applicatif n'a été changé entre les paliers pour améliorer artificiellement les résultats.", '']
    if args.calibration:
        calibration = Path(args.calibration)
        lines += ['## Étalonnage de l’injecteur', '',
                  'Cible statique `/index.html` de Nginx, sans temporisation et sans traitement métier.', '',
                  '| Utilisateurs | Série | Débit (req/s) | Erreurs (%) | p95 (ms) |', '|---:|---:|---:|---:|---:|']
        for file in sorted(calibration.glob('*-statistiques.csv')):
            row = next(r for r in read_csv(file) if r['label'] == 'Total')
            repetition = file.name.split('-r')[1].split('-')[0]
            lines.append(f"| {row['users']} | {repetition} | {float(row['throughput_rps']):.2f} | {row['error_pct']} | {row['p95_ms']} |")
        lines += ['', 'Le débit statique varie entre les répétitions : ne pas en déduire un plafond précis',
                  'ou une répétabilité statique inférieure à 10 %. Même la borne basse est très supérieure',
                  'au débit applicatif mesuré. Comparer aussi la charge CPU de Java pour écarter une saturation',
                  "de l'injecteur. Les résultats bruts volumineux sont archivés sans perte en `.csv.gz`.",
                  'Le premier essai avec épuisement des ports TCP est marqué invalide et exclu de cette campagne.', '']
    lines += ['## Comparaison VM à compléter', '',
              'Les résultats VM ne sont pas encore disponibles. Aucun écart VM/Docker ne peut être calculé.',
              'Déposer leurs bruts `vm-*.csv` dans le même dossier `charge/resultats/`.',
              'Utiliser le même plan exécuté, comptes, données, durées, machine hôte et budgets de ressources.',
              'Réaliser aussi la seconde série VM/Docker avec ordre inversé dans une même session, comme demandé par le sujet.',
              'Les captures GUI de validation, les mesures de démarrage/mémoire au repos des étapes 10/14',
              'et les courbes comparatives finales restent des livrables distincts.', '',
              '## Traçabilité', '',
              '- Bruts : `../dk-*-r*-*.csv` ; toutes les requêtes, montée comprise.',
              '- Statistiques : `synthese.csv` ; plateau uniquement.',
              '- Relevés serveur : `*-serveur.jsonl` et `*-serveur-synthese.json`.',
              '- Rapports JMeter : `rapport-<utilisateurs>-r<répétition>/index.html`.',
              '- Sauvegardes privées : `.charge-backups/` à la racine du projet, exclues de Git.', '']
    destination = session/'RAPPORT-DOCKER.md'
    destination.write_text('\n'.join(lines), encoding='utf-8')
    print(destination)


if __name__ == '__main__':
    main()
