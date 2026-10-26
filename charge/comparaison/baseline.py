"""Three cold starts and idle measurements, outside JMeter load windows."""
import json,time,pathlib,statistics
from campaign import *

def footprint(deployment):
    names={'vm':{'vboxheadless.exe','virtualboxvm.exe','vboxsvc.exe'},'dk':{'vmmemwsl','vmmem','com.docker.backend.exe','docker desktop.exe','com.docker.proxy.exe'}}[deployment]
    processes=[];unreadable=[]
    for p in psutil.process_iter(['pid','name']):
        if p.info['name'].lower() in names:
            try:processes.append({'pid':p.pid,'name':p.info['name'],'rss_bytes':p.memory_info().rss})
            except (psutil.NoSuchProcess,psutil.AccessDenied):unreadable.append(p.info)
    return {'processes':processes,'unreadable':unreadable,'rss_sum_bytes':sum(x['rss_bytes'] for x in processes),'host_used_memory_bytes':psutil.virtual_memory().used,'docker_linux_vm_visible':any(x['name'].lower() in ('vmmem','vmmemwsl') for x in processes)}

def measure(deployment):
    results=[]
    for i in range(1,4):
        if deployment=='vm':stop_vm();stop_docker()
        else:stop_vm();stop_docker()
        time.sleep(8)
        before=footprint(deployment);start_time=time.perf_counter();start(deployment);boot=time.perf_counter()-start_time
        time.sleep(15)
        idlepath=FOLDER/'etapes'/f'{deployment}-baseline-{i}-repos.jsonl'
        monitor=Monitor(deployment,idlepath).start();time.sleep(15);monitor.stop()
        after=footprint(deployment)
        rows=[json.loads(x) for x in idlepath.read_text().splitlines() if x.strip()]
        row={'repetition':i,'date':now(),'boot_seconds':boot,'memory_before':before,'memory_idle':after,'memory_host_delta_bytes':after['host_used_memory_bytes']-before['host_used_memory_bytes'],'service_memory_bytes_mean':{s:mean(r['services'][s]['memory_bytes'] for r in rows if s in r.get('services',{}) and 'memory_bytes' in r['services'][s]) for s in ['db','backend','frontend']},'measurement_definition':'All three VM poweroff to HTTP health=ok' if deployment=='vm' else 'Docker Desktop engine stopped to engine+3 containers HTTP health=ok'}
        results.append(row);write(FOLDER/'etapes'/f'{deployment}-baseline-{i}.json',row)
        print(deployment,'baseline',i,'boot seconds',round(boot,2),flush=True)
    output={'deployment':deployment,'runs':results,'median_boot_seconds':statistics.median(x['boot_seconds'] for x in results),'median_host_rss_sum_bytes':statistics.median(x['memory_idle']['rss_sum_bytes'] for x in results),'median_host_memory_delta_bytes':statistics.median(x['memory_host_delta_bytes'] for x in results),'docker_engine_memory_included':deployment!='dk' or all(x['memory_idle']['docker_linux_vm_visible'] for x in results)}
    write(FOLDER/f'baseline-{deployment}.json',output)
    return output

if __name__=='__main__':
    import sys
    measure(sys.argv[1])
