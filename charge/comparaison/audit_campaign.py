import sys
"""Read-only verification of complete raw samples against reported statistics."""
import csv,json,pathlib,hashlib,collections,math
F=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path(pathlib.Path('D:/Myhike-VM/installation/campagne-active.txt').read_text().strip())
ID=F.name.removeprefix('comparaison-');ROOT=F/'bruts'/'charge'
checks=[]
for d in ['vm','dk']:
    for rep in [1,2]:
        reset=json.loads((F/'etapes'/f'{d}-r{rep}-reset.json').read_text())
        assert reset['reset_from_frozen_sql'] and reset['backup_bytes']>100 # Les sauvegardes privées ne sont pas publiées.
        for n in [1,5,10,25,50,100]:
            stem=f'{d}-{n}-r{rep}-{ID}'
            obj=json.loads((F/'etapes'/f'{stem}-resultat.json').read_text())
            stat=obj['statistics'][0]
            with (ROOT/f'{stem}.csv').open(encoding='utf-8-sig',newline='') as stream:
                raw=list(csv.DictReader(stream))
            assert all(None not in row and all(v is not None for v in row.values()) for row in raw),stem
            selected=[r for r in raw if r['label']!='__measurement_origin' and stat['measurement_start_ms']<=int(r['timeStamp'])<stat['measurement_end_ms']]
            assert len(selected)==stat['samples']
            assert sum(r['success']=='false' for r in selected)==stat['errors']
            elapsed=sorted(int(r['elapsed']) for r in selected)
            ix=(len(elapsed)-1)*.95;lo=math.floor(ix);hi=math.ceil(ix)
            p95=elapsed[lo]+(elapsed[hi]-elapsed[lo])*(ix-lo)
            assert abs(p95-stat['p95_ms'])<.011
            assert abs(len(selected)/60-stat['throughput_rps'])<.0001
            assert obj['server']['collection_errors']==0
            checks.append({'file':stem+'.csv','valid_rows':len(raw),'measured_rows':len(selected),'errors':stat['errors'],'response_codes':dict(collections.Counter(r['responseCode'] for r in selected)),'sha256':hashlib.sha256((ROOT/f'{stem}.csv').read_bytes()).hexdigest(),'verified':True})
manifest=json.loads((F/'configuration.json').read_text())
for name,expected in manifest['hashes'].items():assert hashlib.sha256((F/name).read_bytes()).hexdigest()==expected,name
(F/'rapports'/'verification-donnees.json').write_text(json.dumps({'all_24_load_runs_verified':True,'frozen_inputs_unchanged':True,'checks':checks},ensure_ascii=False,indent=2),encoding='utf-8')
print('Verified all 24 runs, exact windows, counts, errors, p95, throughput, server collection and frozen input hashes.')
