import sys, json, shutil, hashlib, datetime
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path.insert(0,'D:/Myhike/charge')
from prepare_plan import prepare

root=Path('D:/Myhike/charge/resultats')
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
folder=root/f'comparaison-{stamp}';folder.mkdir()
for name in ['captures','etapes','calibration','rapports','graphiques']:(folder/name).mkdir()
for source,target in [('plan.jmx','plan-execute.jmx'),('plan_etalonnage.jmx','plan-etalonnage-execute.jmx')]:
    prepare(Path('D:/Myhike/charge')/source,folder/target)
shutil.copyfile('D:/Myhike/charge/comptes.csv',folder/'comptes.csv')
for name in ['schema.sql','peuplement.sql']:shutil.copyfile(Path('D:/Myhike/donnees')/name,folder/name)
manifest={'id':stamp,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'completion':'preparation','users':[1,5,10,25,50,100],'ramp_seconds':10,'plateau_seconds':60,'duration_seconds':72,'order':['vm-r1','dk-r1','dk-r2','vm-r2'],'resources_per_tier':{'cpus':1,'memory_mb':2048},'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()},'historical_results_preserved':True,'limitations':['Versions OS, Python et MySQL differentes entre les deploiements existants; details dans les configurations.']}
(folder/'configuration.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
(folder/'compose-mesures.yaml').write_text('services:\n  db:\n    cpus: 1.0\n    mem_limit: 2g\n  backend:\n    cpus: 1.0\n    mem_limit: 2g\n  frontend:\n    cpus: 1.0\n    mem_limit: 2g\n')
(folder/'compte-invalide.csv').write_text('email,password\nuser01@refuges.local,INVALID_TEST_PASSWORD\n')
for label,accounts in [('positif','comptes.csv'),('negatif','compte-invalide.csv')]:
    tree=ET.parse(folder/'plan-execute.jmx')
    csvprop=tree.find(".//CSVDataSet/stringProp[@name='filename']");csvprop.text=(folder/accounts).as_posix()
    container=tree.getroot().find('./hashTree/hashTree')
    listener=ET.SubElement(container,'ResultCollector',guiclass='ViewResultsFullVisualizer',testclass='ResultCollector',testname=f'Validation GUI {label}',enabled='true')
    ET.SubElement(listener,'boolProp',name='ResultCollector.error_logging').text='false'
    ET.SubElement(listener,'stringProp',name='filename').text=(folder/'captures'/f'gui-{label}.xml').as_posix()
    ET.SubElement(container,'hashTree')
    tree.write(folder/f'plan-gui-{label}.jmx',encoding='utf-8',xml_declaration=True)
Path('D:/Myhike-VM/installation/campagne-active.txt').write_text(str(folder))
for name in ['VALIDATION-GUI.md','validation-gui.ps1']:
    source=Path(__file__).with_name(name)
    if source.exists():shutil.copyfile(source,folder/name)
protocol=Path(__file__).with_name('PROTOCOLE-COMPARE.md')
if protocol.exists():shutil.copyfile(protocol,folder/'PROTOCOLE.md')
print(folder)
