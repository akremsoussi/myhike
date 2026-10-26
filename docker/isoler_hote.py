"""Isolation complémentaire du moteur Linux natif ; règles limitées au projet Compose."""
import argparse,hashlib,json,os,subprocess

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',default='refuges-validation');p.add_argument('--remove',action='store_true');a=p.parse_args()
    if os.geteuid()!=0:raise SystemExit('Exécuter avec sudo : règles OUTPUT du moteur Linux.')
    chain='REFUGES_'+hashlib.sha256(a.project.encode()).hexdigest()[:10].upper()
    def run(args,check=True):return subprocess.run(args,text=True,capture_output=True,check=check)
    exists=run(['iptables','-w','-nL',chain],False).returncode==0
    jump=['iptables','-w','-C','OUTPUT','-j',chain]
    if a.remove:
        if run(jump,False).returncode==0:run(['iptables','-w','-D','OUTPUT','-j',chain])
        if exists:run(['iptables','-w','-F',chain]);run(['iptables','-w','-X',chain])
        print('Règles de ce projet retirées.');return
    networks=json.loads(run(['docker','network','inspect',a.project+'_web',a.project+'_data']).stdout)
    if not exists:run(['iptables','-w','-N',chain])
    run(['iptables','-w','-F',chain])
    for n in networks:
        for ipam in n['IPAM']['Config']:
            subnet=ipam.get('Subnet','')
            if ':' not in subnet and subnet:run(['iptables','-w','-A',chain,'-d',subnet,'-p','tcp','-m','multiport','--dports','8000,3306,33060','-j','REJECT','--reject-with','tcp-reset'])
    if run(jump,False).returncode:run(['iptables','-w','-I','OUTPUT','1','-j',chain])
    print(run(['iptables','-w','-S',chain]).stdout,end='')

if __name__=='__main__':main()
