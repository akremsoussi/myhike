import argparse, json, time, socket, subprocess, logging
from pathlib import Path
import paramiko
logging.getLogger('paramiko.transport').addHandler(logging.NullHandler())
logging.getLogger('paramiko.transport').propagate=False

ROOT=Path('D:/Myhike-VM'); WORK=ROOT/'installation'; VBOX='D:/virtualBox/VBoxManage.exe'
KEY=paramiko.RSAKey.from_private_key_file(str(WORK/'id_rsa'))
PORTS={'donnees':2230,'metier':2220,'proxy':2210}
IPS={'donnees':'10.10.10.30','metier':'10.10.10.20','proxy':'10.10.10.10'}

def vb(*args):
    p=subprocess.run([VBOX,*map(str,args)],capture_output=True,text=True)
    if p.returncode: raise RuntimeError(p.stdout+p.stderr)
    return p.stdout

def connect(role, jump=False):
    s=paramiko.SSHClient()
    known=WORK/'known_hosts'
    if known.exists(): s.load_host_keys(str(known))
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    proxy=None; sock=None
    if jump:
        proxy=connect('proxy')
        sock=proxy.get_transport().open_channel('direct-tcpip',(IPS[role],22),('127.0.0.1',0),timeout=15)
    s.connect(IPS[role] if jump else '127.0.0.1',port=22 if jump else PORTS[role],username='myhike',pkey=KEY,timeout=8,auth_timeout=15,banner_timeout=15,allow_agent=False,look_for_keys=False,sock=sock)
    s.save_host_keys(str(known)); s._jump=proxy
    return s

def run(s,cmd,timeout=90):
    _,out,err=s.exec_command(cmd,timeout=timeout)
    output=out.read().decode(errors='replace')+err.read().decode(errors='replace')
    code=out.channel.recv_exit_status()
    return code,output
