"""Preuves de la partie 3. Ne supprime aucun volume et ne réinitialise pas la base."""
import argparse,subprocess,json,datetime,hashlib,time,socket,urllib.request,urllib.error,http.cookiejar,secrets
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',default='refuges-validation');p.add_argument('--output',default='docs/preuves-docker/2026-10-26');p.add_argument('--persistence',action='store_true');a=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=root/a.output;out.mkdir(parents=True,exist_ok=True)
    compose=['docker','compose','-p',a.project,'--env-file',str(root/'.env.docker'),'-f',str(root/'docker/compose.yaml')]
    def run(cmd,check=True,input=None,timeout=180):
        r=subprocess.run(cmd,cwd=root,text=True,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
        if check and r.returncode:raise RuntimeError('Commande en échec : '+str(cmd[:4])+'\n'+r.stderr[-2000:])
        return r
    def save(name,data):
        (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n' if not isinstance(data,str) else data,encoding='utf-8')
    def ps():return [json.loads(x) for x in run(compose+['ps','--format','json']).stdout.splitlines() if x]
    services=ps(); ids={x['Service']:x['ID'] for x in services}
    inspect=json.loads(run(['docker','inspect']+list(ids.values())).stdout)
    networks={x['Config']['Labels']['com.docker.compose.service']:x['NetworkSettings']['Networks'] for x in inspect}
    ips={s:next(iter(n.values()))['IPAddress'] for s,n in networks.items()}
    ips['backend_web']=networks['backend'][a.project+'_web']['IPAddress'];ips['backend_data']=networks['backend'][a.project+'_data']['IPAddress']
    save('services.txt',run(compose+['ps']).stdout);save('services.json',services)
    save('reseaux.json',[{'service':s,'networks':{k:{'IPAddress':v['IPAddress'],'Gateway':v['Gateway']} for k,v in n.items()}} for s,n in networks.items()])
    def sql(query):return run(compose+['exec','-T','db','sh','-c','MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -u "$MYSQL_USER" "$MYSQL_DATABASE" --batch --raw',],input=query).stdout
    count_query='SELECT "refuges" AS table_name,COUNT(*) AS nombre FROM refuges UNION ALL SELECT "massifs",COUNT(*) FROM massifs UNION ALL SELECT "communities",COUNT(*) FROM communities UNION ALL SELECT "users",COUNT(*) FROM users; SELECT COUNT(*) AS comptes_charge FROM users WHERE username REGEXP "^user[0-9]{2}$"; SELECT name FROM massifs WHERE name LIKE "%crins%" OR name LIKE "%yr%n%" LIMIT 4;'
    counts=sql(count_query);save('peuplement.txt',counts)
    matrix=[]
    for src in ['frontend','backend','db']:
        for target,port in [('frontend',80),('backend',8000),('db',3306)]:
            if src==target:continue
            ip=ips['backend_data' if src=='db' else 'backend_web'] if target=='backend' else ips[target]
            if src=='backend':
                code='import socket; s=socket.create_connection(('+repr(ip)+','+str(port)+'),2); s.close()'
                cmd=compose+['exec','-T',src,'python','-c',code]
            elif src=='frontend':cmd=compose+['exec','-T',src,'sh','-c',f'nc -w 2 {ip} {port} </dev/null']
            else:cmd=compose+['exec','-T',src,'bash','-c',f'timeout 2 bash -c "exec 3<>/dev/tcp/{ip}/{port}"']
            result=run(cmd,check=False,timeout=8);expected=not ((src=='frontend' and target=='db') or (src=='db' and target=='frontend'))
            matrix.append(dict(source=src,target=target,ip=ip,port=port,expected_reachable=expected,reachable=result.returncode==0,exit_code=result.returncode,stderr=result.stderr.strip()))
    for target,port in [('frontend',80),('backend',8000),('db',3306)]:
        ip='127.0.0.1' if target=='frontend' else ips['backend_web'] if target=='backend' else ips[target];actualport=8080 if target=='frontend' else port
        try:
            with socket.create_connection((ip,actualport),2):reach=True
        except OSError:reach=False
        matrix.append(dict(source='hote_moteur_WSL',target=target,ip=ip,port=actualport,expected_reachable=target=='frontend',reachable=reach))
    save('matrice.json',matrix)
    # Vérification fonctionnelle : login, cookie et liste non vide ; aucune valeur du cookie n'est conservée.
    jar=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req=urllib.request.Request('http://127.0.0.1:8080/api/auth/login',data=json.dumps(dict(email='randonneur@refuges.local',password='refuges123')).encode(),headers={'Content-Type':'application/json'})
    with opener.open(req,timeout=10) as r:login=r.status
    with opener.open('http://127.0.0.1:8080/api/refuges?limit=20',timeout=10) as r:body=json.load(r);consult=r.status
    assert login==200 and consult==200 and body['total']==4652 and len(body['items'])>0
    save('parcours.json',dict(login_http=login,cookie_session_present=any(c.name=='refuges_session' for c in jar),consultation_http=consult,total=body['total'],items=len(body['items'])))
    if a.persistence:
        assert 'validation' in a.project,'Test de persistance réservé à un projet de validation.'
        marker=secrets.token_hex(12)
        sql('CREATE TABLE IF NOT EXISTS preuve_persistance_part3 (id INT PRIMARY KEY, valeur VARCHAR(64)); INSERT INTO preuve_persistance_part3 VALUES (1,"'+marker+'") ON DUPLICATE KEY UPDATE valeur=VALUES(valeur);')
        before={x['Config']['Labels']['com.docker.compose.service']:dict(id=x['Id'],mounts=[{'Name':m.get('Name'),'Destination':m['Destination']} for m in x['Mounts'] if m['Type']=='volume']) for x in inspect}
        run(compose+['up','-d','--force-recreate','--wait'],timeout=180)
        after_services=ps();after=json.loads(run(['docker','inspect']+[s['ID'] for s in after_services]).stdout)
        value=sql('SELECT valeur FROM preuve_persistance_part3 WHERE id=1;').splitlines()[-1]
        assert value==marker;assert sql(count_query)==counts
        sql('DROP TABLE preuve_persistance_part3;')
        after_map={x['Config']['Labels']['com.docker.compose.service']:dict(id=x['Id'],mounts=[{'Name':m.get('Name'),'Destination':m['Destination']} for m in x['Mounts'] if m['Type']=='volume']) for x in after}
        assert all(before[s]['id']!=after_map[s]['id'] for s in before)
        save('persistance.json',dict(before=before,after=after_map,marker_retained=True,business_counts_unchanged=True,test_table_removed=True,volumes_deleted=False))
        save('services-apres-recreation.txt',run(compose+['ps']).stdout)
    image_ids=sorted(set(x['Image'] for x in json.loads(run(['docker','inspect']+[s['ID'] for s in ps()]).stdout)))
    images=json.loads(run(['docker','image','inspect']+image_ids).stdout)
    save('images.json',[dict(id=x['Id'],tags=x.get('RepoTags'),digests=x.get('RepoDigests'),size_bytes=x['Size']) for x in images])
    save('versions.txt',run(['docker','version']).stdout+run(['docker','compose','version']).stdout)
    save('configuration.json',dict(date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project=a.project,source_commit=run(['git','-c','safe.directory='+str(root),'rev-parse','HEAD']).stdout.strip(),files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'docker/compose.yaml',root/'docker/metier.Dockerfile',root/'docker/proxy.Dockerfile',root/'metier/requirements.lock',root/'donnees/schema.sql',root/'donnees/peuplement.sql']}))
    assert all(x['reachable']==x['expected_reachable'] for x in matrix),'Isolation incomplète ; consulter matrice.json et isoler_hote.py sur Linux natif.'
    print(json.dumps(matrix,ensure_ascii=False,indent=2));print('Preuves enregistrées dans',out)

if __name__=='__main__':main()
