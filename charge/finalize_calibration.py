"""Archive complete calibration runs and collect their server summaries."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('session')
    args = parser.parse_args()
    session = Path(args.session)
    config = json.loads((session/'configuration.json').read_text(encoding='utf-8-sig'))
    if config['completion'] != 'complete':
        raise ValueError('Calibration has not completed')
    for statistics in session.glob('*-statistiques.csv'):
        stem = statistics.name.removesuffix('-statistiques.csv')
        raw = session.parent/(stem+'.csv')
        compressed = Path(str(raw)+'.gz')
        if not compressed.exists():
            with raw.open('rb') as source, gzip.open(compressed, 'wb') as target:
                shutil.copyfileobj(source, target)
        subprocess.run([sys.executable, str(Path(__file__).with_name('server_summary.py')),
                        str(session/(stem+'-serveur.jsonl')), str(statistics),
                        str(session/(stem+'-serveur-synthese.json'))], check=True)
    print('Calibration archived and server measurements verified.')


if __name__ == '__main__':
    main()
