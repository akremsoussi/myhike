"""Paired VM/Docker JMeter protocol. Raw results are never overwritten."""
import argparse, concurrent.futures, csv, datetime, gzip, hashlib, json, os, pathlib, shutil, socket, subprocess, sys, threading, time, urllib.request
import psutil
from statistics import mean
sys.path.insert(0,'D:/Myhike/charge')
from summarize import summarize
from server_summary import byte_count
from control import connect,run as remote,vb

REPO=pathlib.Path('D:/Myhike'); ROOT=pathlib.Path('D:/Myhike/charge/resultats')
FOLDER=pathlib.Path(pathlib.Path('D:/Myhike-VM/installation/campagne-active.txt').read_text().strip())
ID=FOLDER.name.removeprefix('comparaison-')
JAVA='C:/Program Files/Java/jre1.8.0_511/bin/java.exe'
JAR='C:/Users/souss/Downloads/apache-jmeter-5.6.3/bin/ApacheJMeter.jar'
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
COMPOSE=[DOCKER,'compose','--env-file',str(REPO/'.env.docker'),'-f',str(REPO/'docker/compose.yaml'),'-f',str(FOLDER/'compose-mesures.yaml')]
LEVELS=[1,5,10,25,50,100]
ROLES=['donnees','metier','proxy']
SERVICES={'donnees':'db','metier':'backend','proxy':'frontend'}

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(path,obj):pathlib.Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def cmd(args,timeout=180,check=True,input=None):
    p=subprocess.run(list(map(str,args)),input=input,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW)
    if check and p.returncode:raise RuntimeError('Command failed: '+str(args[:3])+'\n'+p.stdout[-2000:]+p.stderr[-2000:])
    return p
def docker(*args,**kw):return cmd([DOCKER,*args],**kw)
def compose(*args,**kw):return cmd(COMPOSE+list(args),**kw)
def health():
    try:
        with urllib.request.urlopen('http://127.0.0.1:8080/api/health',timeout=4) as r:return json.load(r).get('database')=='ok'
    except Exception:return False
def wait_health():
    for _ in range(100):
        if health():return
        time.sleep(3)
    raise RuntimeError('Health check unavailable')
def vm_running():return any('"vm-'+r+'"' in vb('list','runningvms') for r in ROLES)
def docker_running():return docker('info','--format','{{.ServerVersion}}',check=False,timeout=15).returncode==0

def stop_vm():
    names=vb('list','runningvms')
    for r in reversed(ROLES):
        if '"vm-'+r+'"' in names:vb('controlvm','vm-'+r,'acpipowerbutton')
    for _ in range(90):
        if not vm_running():return
        time.sleep(2)
    raise RuntimeError('VM shutdown failed')

def stop_docker():
    if not docker_running():return
    ids=docker('ps','-q').stdout.split()
    active=json.loads(docker('inspect',*ids).stdout) if ids else []
    others=[x['Name'] for x in active if (x['Config'].get('Labels') or {}).get('com.docker.compose.project')!='refuges']
    if others:raise RuntimeError('Other containers active; will not stop them: '+', '.join(others))
    compose('stop')
    docker('desktop','stop','--timeout','180',timeout=200)
    for _ in range(30):
        if not docker_running():return
        time.sleep(2)
    raise RuntimeError('Docker engine still running during VM tests')

def start(deployment):
    if deployment=='vm':
        stop_docker()
        for r in ROLES:
            if 'VMState="running"' not in vb('showvminfo','vm-'+r,'--machinereadable'):vb('startvm','vm-'+r,'--type','headless')
    else:
        stop_vm()
        if not docker_running():docker('desktop','start','--timeout','240',timeout=260)
        if not (FOLDER/'docker-build.txt').exists():
            build=compose('build',timeout=900)
            (FOLDER/'docker-build.txt').write_text(build.stdout+build.stderr,encoding='utf-8')
        ready=compose('up','-d','--wait',timeout=300,check=False)
        if ready.returncode:
            # Recovery is between campaigns only, never within a measured palier.
            if 'backend' not in ready.stderr or 'unhealthy' not in ready.stderr:raise RuntimeError(ready.stdout+ready.stderr)
            stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            states=json.loads(docker('inspect',*compose('ps','-a','-q').stdout.split()).stdout)
            write(FOLDER/'etapes'/f'dk-recovery-{stamp}.json',{'reason':ready.stdout+ready.stderr,'date':now(),'states':[{'Name':x['Name'],'State':x['State']} for x in states],'action':'restart backend between campaigns before next database reset'})
            compose('restart','backend')
            compose('up','-d','--wait',timeout=300)
    wait_health()
    print(now(),deployment,'ready, other deployment stopped',flush=True)

def sshs():return {r:connect(r,jump=r!='proxy') for r in ROLES}
def close(ss):
    for s in ss.values():
        jump=getattr(s,'_jump',None);s.close()
        if jump:jump.close()
def checked(s,command,timeout=180):
    code,out=remote(s,command,timeout)
    if code:raise RuntimeError(out[-3000:])
    return out

def reset(deployment,rep):
    backup=REPO/'.charge-backups'/f'{deployment}-{ID}-r{rep}.sql'
    backup.parent.mkdir(exist_ok=True)
    if backup.exists():raise RuntimeError('Backup exists; refusing duplicate reset')
    if deployment=='vm':
        ss=sshs()
        try:
            checked(ss['metier'],'sudo systemctl stop refuges-backend')
            dump=checked(ss['donnees'],'sudo mysqldump --single-transaction --no-tablespaces --default-character-set=utf8mb4 refuges',300)
            if len(dump)<100:raise RuntimeError('Empty backup')
            backup.write_text(dump,encoding='utf-8')
            sf=ss['donnees'].open_sftp()
            for n in ['schema.sql','peuplement.sql']:sf.put(str(FOLDER/n),'/home/myhike/charge-'+n)
            sf.close()
            checked(ss['donnees'],'''sudo mysql -e 'DROP DATABASE refuges; CREATE DATABASE refuges CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;' && sudo mysql --default-character-set=utf8mb4 refuges < /home/myhike/charge-schema.sql && sudo mysql --default-character-set=utf8mb4 refuges < /home/myhike/charge-peuplement.sql''',300)
            checked(ss['donnees'],'sudo systemctl restart mysql')
            checked(ss['metier'],'sudo systemctl start refuges-backend')
        finally:close(ss)
    else:
        compose('stop','frontend','backend')
        dump=compose('exec','-T','db','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump -uroot --single-transaction --no-tablespaces --default-character-set=utf8mb4 "$MYSQL_DATABASE"',timeout=300).stdout
        if len(dump)<100:raise RuntimeError('Empty Docker backup')
        backup.write_text(dump,encoding='utf-8')
        for n in ['schema.sql','peuplement.sql']:compose('cp',str(FOLDER/n),'db:/tmp/charge-'+n)
        compose('exec','-T','db','sh','-c','export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"; mysql -uroot -e "DROP DATABASE refuges; CREATE DATABASE refuges CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;" && mysql -uroot --default-character-set=utf8mb4 refuges < /tmp/charge-schema.sql && mysql -uroot --default-character-set=utf8mb4 refuges < /tmp/charge-peuplement.sql',timeout=300)
        compose('restart','db');compose('up','-d','--wait',timeout=300)
    wait_health()
    write(FOLDER/'etapes'/f'{deployment}-r{rep}-reset.json',{'date':now(),'backup':str(backup),'backup_bytes':backup.stat().st_size,'reset_from_frozen_sql':True})
    print(now(),deployment,'r'+str(rep),'database backed up and reset',flush=True)

def host_sample(previous):
    java=[];virtual=[]
    for p in psutil.process_iter(['pid','name','memory_info','cpu_times']):
        try:
            n=p.info['name'].lower()
            if n in ('java.exe','javaw.exe'):
                c=p.info['cpu_times'];m=p.info['memory_info'];java.append({'pid':p.pid,'cpu':c.user+c.system,'rss':m.rss})
            if n in ('vboxheadless.exe','virtualboxvm.exe','vmmemwsl','vmmem','com.docker.backend.exe'):
                virtual.append({'name':n,'pid':p.pid,'rss':p.info['memory_info'].rss})
        except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    t=time.time();cpu=0
    for p in java:
        old=previous.get(p['pid'])
        if old:cpu+=max(0,p['cpu']-old[1])/(t-old[0])*100/psutil.cpu_count()
        previous[p['pid']]=(t,p['cpu'])
    return {'java_cpu_percent_host':cpu,'java_working_set_bytes':sum(p['rss'] for p in java),'java_process_count':len(java),'host_cpu_percent':psutil.cpu_percent(),'host_available_memory_bytes':psutil.virtual_memory().available,'virtualization_processes':virtual}

class Monitor:
    def __init__(self,deployment,path):
        self.deployment=deployment;self.path=path;self.event=threading.Event();self.errors=[];self.previous={};self.prev_services={};self.ss=None;self.latest={};self.readers=[];self.streams=[]
    def start(self):
        if self.deployment=='vm':
            self.ss=sshs()
            src=pathlib.Path(__file__).with_name('guest_metrics.py')
            for s in self.ss.values():
                sf=s.open_sftp();sf.put(str(src),'/home/myhike/charge-metrics.py');sf.close()
            for role,s in self.ss.items():
                _,stdout,stderr=s.exec_command('sudo python3 -u /home/myhike/charge-metrics.py '+role+' --stream')
                self.streams.append(stdout)
                def consume(role=role,stdout=stdout):
                    try:
                        for line in stdout:
                            if self.event.is_set():break
                            self.latest[role]=(time.time(),json.loads(line))
                    except Exception as exc:
                        if not self.event.is_set():self.errors.append(str(exc))
                reader=threading.Thread(target=consume,daemon=True);reader.start();self.readers.append(reader)
            for _ in range(100):
                if len(self.latest)==3:break
                time.sleep(.2)
            else:raise RuntimeError('VM streaming collectors did not start')
        self.thread=threading.Thread(target=self.loop,daemon=True);self.thread.start();return self
    def sample(self):
        t=time.time();item={'timestamp_utc':now(),'timestamp_ms':int(t*1000),**host_sample(self.previous)}
        if self.deployment=='vm':
            if any(time.time()-v[0]>12 for v in self.latest.values()):raise RuntimeError('Stale VM metrics')
            raw={r:v[1] for r,v in self.latest.items()}
            item['vm_raw']=raw;item['services']={}
            for role,r in raw.items():
                if 'service_unavailable' in r:
                    item['services'][SERVICES[role]]={'unavailable':r['service_unavailable']}
                    continue
                old=self.prev_services.get(role);cpu=None;guest=None
                if old and r['timestamp']>old['timestamp']:
                    dt=r['timestamp']-old['timestamp'];cpu=(r['service_cpu_usec']-old['service_cpu_usec'])/1e6/dt*100
                    total=r['guest_cpu_total']-old['guest_cpu_total'];guest=100*(1-(r['guest_cpu_idle']-old['guest_cpu_idle'])/total) if total else 0
                self.prev_services[role]=r
                item['services'][SERVICES[role]]={'cpu_percent':cpu,'memory_bytes':r['memory_bytes'],'block_read_bytes':r['block_read_bytes'],'block_written_bytes':r['block_written_bytes'],'guest_cpu_percent':guest,'guest_memory_used_bytes':r['guest_memory_used_bytes']}
            item['mysql']=raw['donnees'].get('mysql',{})
        else:
            stats=compose('stats','--no-stream','--format','{{json .}}',timeout=30).stdout
            item['services']={}
            for line in stats.splitlines():
                s=json.loads(line);name=next(x for x in ['backend','frontend','db'] if '-'+x+'-' in s['Name']);read,written=s['BlockIO'].split('/')
                item['services'][name]={'cpu_percent':float(s['CPUPerc'].rstrip('%')),'memory_bytes':byte_count(s['MemUsage'].split('/')[0]),'block_read_bytes':byte_count(read),'block_written_bytes':byte_count(written)}
            sql="SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_connected','Threads_running','Innodb_data_reads','Innodb_data_writes','Innodb_data_read','Innodb_data_written');"
            output=compose('exec','-T','db','sh','-c','MYSQL_PWD="$MYSQL_PASSWORD" mysql --batch --skip-column-names -u"$MYSQL_USER" "$MYSQL_DATABASE"',input=sql,timeout=20).stdout
            item['mysql']={k:int(v) for k,v in (line.split('\t') for line in output.splitlines())}
            for name in ['db','backend','frontend']:
                if name not in item['services']:item['services'][name]={'unavailable':'Container absent from docker stats; see inspect evidence'}
        return item
    def loop(self):
        with self.path.open('w',encoding='utf-8') as out:
            while not self.event.is_set():
                try:item=self.sample()
                except Exception as exc:
                    self.errors.append(str(exc));item={'timestamp_utc':now(),'timestamp_ms':int(time.time()*1000),'error':str(exc)}
                out.write(json.dumps(item)+'\n');out.flush();self.event.wait(3)
    def stop(self):
        self.event.set();self.thread.join(70)
        for stream in self.streams:stream.channel.close()
        if self.ss:close(self.ss)
        if self.thread.is_alive():raise RuntimeError('Monitor did not terminate')

def server_summary(path,stats,destination):
    rows=[json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]
    start,end=stats['measurement_start_ms'],stats['measurement_end_ms'];rows=[r for r in rows if start<=r['timestamp_ms']<end]
    if len(rows)<5 or any('error' in r for r in rows):raise RuntimeError('Incomplete monitoring: '+str([r for r in rows if 'error' in r]))
    services={}
    for service in ['db','backend','frontend']:
        values=[r['services'][service] for r in rows]
        services[service]={}
        for field in ['cpu_percent','memory_bytes','guest_cpu_percent','guest_memory_used_bytes']:
            nums=[v[field] for v in values if v.get(field) is not None]
            if nums:services[service][field+'_mean']=mean(nums);services[service][field+'_max']=max(nums)
        for field in ['block_read_bytes','block_written_bytes']:
            nums=[v[field] for v in values if field in v];services[service][field+'_delta']=max(nums)-min(nums) if nums else None
        services[service]['unavailable_samples']=sum('unavailable' in v for v in values)
    result={'users':stats['users'],'samples':len(rows),'collection_errors':0,'measurement_start_ms':start,'measurement_end_ms':end,'services':services,'java_cpu_percent_host_mean':mean(r['java_cpu_percent_host'] for r in rows),'java_cpu_percent_host_max':max(r['java_cpu_percent_host'] for r in rows),'java_working_set_bytes_max':max(r['java_working_set_bytes'] for r in rows),'host_available_memory_bytes_min':min(r['host_available_memory_bytes'] for r in rows),'host_cpu_percent_max':max(r['host_cpu_percent'] for r in rows)}
    for field in ['Threads_connected','Threads_running']:
        vals=[r['mysql'][field] for r in rows if field in r.get('mysql',{})];result[field+'_mean']=mean(vals) if vals else None;result[field+'_max']=max(vals) if vals else None
    for field in ['Innodb_data_read','Innodb_data_written']:
        vals=[r['mysql'][field] for r in rows if field in r.get('mysql',{})];result[field+'_delta']=max(vals)-min(vals) if vals else None
    write(destination,result);return result

def jmeter(args,stem,timeout=170):
    with pathlib.Path(str(stem)+'.stdout.log').open('w',encoding='utf-8') as out:
        p=subprocess.Popen([JAVA,'-Xms1g','-Xmx1g','-XX:MaxMetaspaceSize=256m','-XX:+UseG1GC','-XX:MaxGCPauseMillis=100','-XX:G1ReservePercent=20','-Djava.security.egd=file:/dev/urandom','-Duser.language=en','-Duser.region=EN','-jar','ApacheJMeter.jar',*map(str,args)],cwd=str(pathlib.Path(JAR).parent),stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        try:rc=p.wait(timeout)
        except subprocess.TimeoutExpired:p.kill();p.wait();raise RuntimeError('JMeter timeout')
    if rc:raise RuntimeError('JMeter failed: '+str(stem))

def controls(deployment,rep):
    for label,accounts in [('positif','comptes.csv'),('negatif','compte-invalide.csv')]:
        raw=FOLDER/'etapes'/f'{deployment}-r{rep}-{label}.csv'
        jmeter(['-n','-t',FOLDER/'plan-execute.jmx',f'-Jcomptes={(FOLDER/accounts).as_posix()}','-Jhost=127.0.0.1','-Jport=8080','-Jutilisateurs=1','-Jmontee=1','-Jboucles=1','-Jduree=60','-l',raw,'-j',str(raw)+'.jmeter.log'],raw,90)
        with raw.open() as f:rows=[r for r in csv.DictReader(f) if r['label']!='__measurement_origin']
        if label=='positif' and (len(rows)!=2 or any(r['success']!='true' for r in rows)):raise RuntimeError('Positive control failed')
        if label=='negatif' and not any(r['label']=='01 - Connexion' and r['success']=='false' for r in rows):raise RuntimeError('Negative control failed')
    print(now(),deployment,rep,'positive and negative controls OK',flush=True)

def configuration(deployment,rep):
    folder=FOLDER/'etapes'/f'{deployment}-r{rep}-configuration';folder.mkdir(exist_ok=True)
    if deployment=='vm':
        ss=sshs()
        try:
            for role in ROLES:
                (folder/(role+'-virtualbox.txt')).write_text(vb('showvminfo','vm-'+role,'--machinereadable'))
                output=checked(ss[role],"cat /etc/os-release; uname -r; nproc; free -b; date -u +%s; "+{'donnees':'mysql --version','metier':'/opt/myhike/.venv/bin/pip freeze; python3 --version','proxy':'nginx -v; cat /opt/myhike/version-node.txt'}[role])
                (folder/(role+'-versions.txt')).write_text(output,encoding='utf-8')
        finally:close(ss)
    else:
        (folder/'docker-version.txt').write_text(docker('version').stdout)
        ids=compose('ps','-q').stdout.split()
        inspect=json.loads(docker('inspect',*ids).stdout)
        safe=[{'Name':x['Name'],'Image':x['Image'],'HostConfig':{k:x['HostConfig'].get(k) for k in ['NanoCpus','Memory','MemorySwap']}} for x in inspect]
        assert all(x['HostConfig']['NanoCpus']==1000000000 and x['HostConfig']['Memory']==2147483648 for x in safe)
        write(folder/'resources.json',safe)
        (folder/'backend-versions.txt').write_text(compose('exec','-T','backend','sh','-c','python --version; pip freeze').stdout)
        (folder/'db-versions.txt').write_text(compose('exec','-T','db','mysql','--version').stdout)
        (folder/'frontend-versions.txt').write_text(compose('exec','-T','frontend','nginx','-v').stderr)
    processes=[]
    for p in psutil.process_iter(['name','memory_info']):
        try:processes.append({'name':p.info['name'],'rss':p.info['memory_info'].rss})
        except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    write(folder/'host.json',{'cpu_count':psutil.cpu_count(),'memory':dict(psutil.virtual_memory()._asdict()),'processes':processes})

def sample_run(deployment,rep,users,calibration=False):
    prefix=('etalonnage-' if calibration else '')+deployment
    stem=f'{prefix}-{users}-r{rep}-{ID}'
    raw=FOLDER/'bruts'/('etalonnage' if calibration else 'charge')/(stem+'.csv');raw.parent.mkdir(parents=True,exist_ok=True);out=FOLDER/('calibration' if calibration else 'etapes')
    if raw.exists():raise RuntimeError('Refusing overwrite '+str(raw))
    monitor=Monitor(deployment,out/(stem+'-serveur.jsonl')).start()
    print(now(),stem,'START 10s ramp + 60s measured',flush=True)
    try:
        jmeter(['-n','-t',FOLDER/('plan-etalonnage-execute.jmx' if calibration else 'plan-execute.jmx'),f'-Jcomptes={(FOLDER/"comptes.csv").as_posix()}','-Jhost=127.0.0.1','-Jport=8080',f'-Jutilisateurs={users}','-Jmontee=10','-Jboucles=-1','-Jduree=72','-Jpath=/index.html','-Jjmeter.save.saveservice.output_format=csv','-Jjmeter.save.saveservice.timestamp_format=ms','-Jjmeter.save.saveservice.thread_counts=true','-l',raw,'-j',out/(stem+'.jmeter.log')],out/stem)
    finally:monitor.stop()
    if 'java.net.BindException' in raw.read_text(encoding='utf-8'):raise RuntimeError('Injector TCP port exhaustion')
    steady=out/(stem+'-plateau.csv');stats=summarize(raw,steady,10,60,users)
    with (out/(stem+'-statistiques.csv')).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=stats[0]);w.writeheader();w.writerows(stats)
    server=server_summary(monitor.path,stats[0],out/(stem+'-serveur-synthese.json'))
    result={'deployment':deployment,'repetition':rep,'calibration':calibration,'monitoring_method':'persistent-stream-v2','raw':str(raw),'statistics':stats,'server':server}
    write(out/(stem+'-resultat.json'),result)
    print(now(),stem,'DONE',json.dumps(stats[0]),flush=True)
    if calibration:
        with raw.open('rb') as source,gzip.open(str(raw)+'.gz','wb') as target:shutil.copyfileobj(source,target)
    else:
        if deployment=='vm':
            s=connect('metier',jump=True);log=checked(s,'sudo journalctl -u refuges-backend --since "5 minutes ago" --no-pager; sudo journalctl -k --since "5 minutes ago" --no-pager',60);s.close()
        else:
            log=compose('logs','--no-color','--since','5m','backend').stdout
            inspected=json.loads(docker('inspect',*compose('ps','-a','-q').stdout.split()).stdout)
            write(out/(stem+'-container-states.json'),[{'Name':x['Name'],'State':x['State']} for x in inspected])
        (out/(stem+'-backend.txt')).write_text(log,encoding='utf-8')
    time.sleep(10)
    return result

def stage(deployment,rep,calibration=False):
    start(deployment);configuration(deployment,rep)
    if calibration:
        for n in [20,100]:sample_run(deployment,rep,n,True)
    else:
        reset(deployment,rep);controls(deployment,rep)
        idle=Monitor(deployment,FOLDER/'etapes'/f'{deployment}-r{rep}-repos.jsonl').start();time.sleep(12);idle.stop()
        for n in LEVELS:sample_run(deployment,rep,n)
    suffix='calibration' if calibration else 'campagne'
    write(FOLDER/'etapes'/f'{deployment}-r{rep}-{suffix}.json',{'completion':'complete','date':now()})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('deployment',choices=['vm','dk']);p.add_argument('--rep',type=int,required=True);p.add_argument('--calibration',action='store_true');p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    if a.prepare_only:start(a.deployment);configuration(a.deployment,a.rep)
    else:stage(a.deployment,a.rep,a.calibration)
