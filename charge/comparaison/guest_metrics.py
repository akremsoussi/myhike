"""Linux service metrics, collected read-only over SSH (no extra packages)."""
import json, pathlib, subprocess, sys, time
def pairs(path):
    return {p[0]:int(p[1]) for line in path.read_text().splitlines() if len(p:=line.split())==2}
def sample(role):
    unit={'donnees':'mysql.service','metier':'refuges-backend.service','proxy':'nginx.service'}[role]
    cg=pathlib.Path('/sys/fs/cgroup/system.slice')/unit
    cpu=pairs(cg/'cpu.stat'); ms=pairs(cg/'memory.stat')
    io={'read':0,'write':0}
    for line in (cg/'io.stat').read_text().splitlines():
        row=dict(x.split('=') for x in line.split()[1:])
        io['read']+=int(row.get('rbytes',0));io['write']+=int(row.get('wbytes',0))
    mem={}
    for line in pathlib.Path('/proc/meminfo').read_text().splitlines():
        key,val=line.split(':',1);mem[key]=int(val.strip().split()[0])*1024
    stat=[int(x) for x in pathlib.Path('/proc/stat').read_text().splitlines()[0].split()[1:]]
    result={'timestamp':time.time(),'role':role,'service_cpu_usec':cpu['usage_usec'],'memory_bytes':max(0,int((cg/'memory.current').read_text())-ms.get('inactive_file',0)), 'block_read_bytes':io['read'],'block_written_bytes':io['write'], 'guest_memory_used_bytes':mem['MemTotal']-mem['MemAvailable'],'guest_memory_total_bytes':mem['MemTotal'],'guest_cpu_total':sum(stat[:8]),'guest_cpu_idle':stat[3]+stat[4]}
    if role=='donnees':
        sql="SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_connected','Threads_running','Innodb_data_reads','Innodb_data_writes','Innodb_data_read','Innodb_data_written');"
        p=subprocess.run(['mysql','--batch','--skip-column-names','-e',sql],capture_output=True,text=True,check=True)
        result['mysql']={k:int(v) for k,v in (line.split('\t') for line in p.stdout.splitlines())}
    return result
if __name__=='__main__':
    while True:
        try:result=sample(sys.argv[1])
        except (FileNotFoundError,subprocess.CalledProcessError) as exc:
            result={'timestamp':time.time(),'role':sys.argv[1],'service_unavailable':str(exc)}
        print(json.dumps(result),flush=True)
        if '--stream' not in sys.argv:break
        time.sleep(3)
