import sys
"""Generate the comparison from measured files only, after all load runs."""
import csv,json,pathlib,statistics,hashlib,shutil,datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from xml.sax.saxutils import escape

ROOT=pathlib.Path('D:/Myhike/charge/resultats')
F=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path(pathlib.Path('D:/Myhike-VM/installation/campagne-active.txt').read_text().strip())
ID=F.name.removeprefix('comparaison-'); DATE=ID[6:8]+'/'+ID[4:6]+'/'+ID[:4]; LEVELS=[1,5,10,25,50,100]
OUT=F/'rapports'; OUT.mkdir(exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
mean=statistics.mean
def variation(a,b):return abs(a-b)/mean([a,b])*100 if a+b else 0
def fmt(x,n=2):return f'{x:.{n}f}'.replace('.',',')
def writecsv(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

data={}; rows=[]; reps=[]; calibration=[]
for d in ['vm','dk']:
    for n in LEVELS:
        pair=[]
        for r in [1,2]:
            obj=load(F/'etapes'/f'{d}-{n}-r{r}-{ID}-resultat.json')
            s=obj['statistics'][0];s=dict(s);s['successful_rps']=(s['samples']-s['errors'])/60
            data[d,n,r]={'stats':s,'server':obj['server']}
            row={'deployment':d,'repetition':r,**s}
            row['backend_cpu_mean']=obj['server']['services']['backend'].get('cpu_percent_mean')
            row['db_cpu_mean']=obj['server']['services']['db'].get('cpu_percent_mean')
            row['db_connections_max']=obj['server'].get('Threads_connected_max')
            rows.append(row);pair.append(s)
        reps.append({'deployment':d,'users':n,'throughput_variation_pct':variation(*[s['throughput_rps'] for s in pair]),'p95_variation_pct':variation(*[s['p95_ms'] for s in pair]),'errors_r1_pct':pair[0]['error_pct'],'errors_r2_pct':pair[1]['error_pct']})
    for n in [20,100]:
        for r in [1,2]:
            obj=load(F/'calibration'/f'etalonnage-{d}-{n}-r{r}-{ID}-resultat.json')
            calibration.append({'deployment':d,'users':n,'repetition':r,**obj['statistics'][0]})
writecsv(OUT/'synthese.csv',rows);writecsv(OUT/'repetabilite.csv',reps);writecsv(OUT/'etalonnage.csv',calibration)
baseline={d:load(F/f'baseline-{d}.json') for d in ['vm','dk']}
def avg(d,n,key):return mean(data[d,n,r]['stats'][key] for r in [1,2])
best={d:max([n for n in LEVELS if all(data[d,n,r]['stats']['errors']==0 for r in [1,2])],key=lambda n:avg(d,n,'successful_rps')) for d in ['vm','dk']}
unstable=[f"{x['deployment'].upper()} {x['users']} u." for x in reps if max(x['throughput_variation_pct'],x['p95_variation_pct'])>10]
maxmem={d:max(data[d,n,r]['server']['services']['backend'].get('memory_bytes_max',0) for n in LEVELS for r in [1,2])/2**20 for d in ['vm','dk']}
for metric,label,name in [('throughput_rps','Débit total (requêtes/s)','debit'),('p95_ms','p95 (secondes)','latence'),('error_pct','Requêtes en erreur (%)','erreurs')]:
    fig,ax=plt.subplots(figsize=(8.2,2.45),layout='constrained')
    for d,c in [('vm','#2463A0'),('dk','#D36723')]:
        for r in [1,2]:
            vals=[data[d,n,r]['stats'][metric]/(1000 if metric=='p95_ms' else 1) for n in LEVELS]
            ax.plot(range(6),vals,marker='o',color=c,linestyle='-' if r==1 else '--',label=f'{d.upper()} r{r}',linewidth=1.6,markersize=4)
    ax.set_xticks(range(6),LEVELS);ax.set_xlabel('Utilisateurs simultanés');ax.set_ylabel(label);ax.grid(alpha=.2);ax.set_ylim(bottom=0)
    ax.legend(ncol=4,fontsize=8,loc='upper left');fig.savefig(F/'graphiques'/f'{name}.png',dpi=180);plt.close(fig)

protocol=("Même poste Windows, même code applicatif, mêmes fichiers SQL et comptes figés, même plan JMeter 5.6.3 / Java 8u511. "
"Chaque couche dispose de 1 CPU et 2 Gio de RAM (système invité compris pour les VM). Un seul déploiement fonctionne à la fois ; Docker Desktop est arrêté pendant les mesures VM. "
"L'ordre des campagnes est VM r1, Docker r1, Docker r2, VM r2. Une sauvegarde privée et une réinitialisation SQL précèdent chaque série.")
scenario=("Une itération ouvre une session puis consulte 20 refuges authentifiés ; assertions HTTP, contenu et session, attente de 500 à 1 000 ms avant chaque requête. "
"Paliers : 1, 5, 10, 25, 50 et 100 utilisateurs. Montée 10 s, fenêtre mesurée 60 s après le marqueur + 11 s, pause 10 s entre paliers. "
"Les requêtes sont retenues par leur heure de départ ; leur durée complète est conservée. Les contrôles positif et mot de passe incorrect sont archivés pour chaque série.")
caltext=' '.join(f"{d.upper()} : {fmt(min(x['throughput_rps'] for x in calibration if x['deployment']==d),0)} à {fmt(max(x['throughput_rps'] for x in calibration if x['deployment']==d),0)} req/s sur /index.html." for d in ['vm','dk'])
caltext+=' Ce sont des bornes de capacité du couple injecteur/proxy, pas une mesure isolée du plafond de Java. Les métriques de Java et les erreurs sont conservées.'
summary=[['Grandeur','VM','Docker']]
summary.append(['Meilleur débit observé sans erreur',*[f"{fmt(avg(d,best[d],'successful_rps'))} req/s ({best[d]} u.)" for d in ['vm','dk']]])
summary.append(['p95 moyen à 10 utilisateurs',*[f"{fmt(avg(d,10,'p95_ms')/1000)} s" for d in ['vm','dk']]])
summary.append(['Erreurs moyennes à 100 utilisateurs',*[f"{fmt(avg(d,100,'error_pct'))} %" for d in ['vm','dk']]])
summary.append(['Premier palier proche du plateau (1)',*[str(next(n for n in LEVELS if avg(d,n,'successful_rps')>=.9*avg(d,best[d],'successful_rps')))+' utilisateurs' for d in ['vm','dk']]])
summary.append(['Composant limitant observé','Backend : CPU / pool','Backend : CPU / pool'])
summary.append(['Démarrage complet, médiane de 3',*[f"{fmt(baseline[d]['median_boot_seconds'])} s" for d in ['vm','dk']]])
summary.append(['Somme RSS hôte au repos, médiane',*[f"{fmt(baseline[d]['median_host_rss_sum_bytes']/2**20,0)} Mio" + (' *' if d=='dk' and not baseline[d]['docker_engine_memory_included'] else '') for d in ['vm','dk']]])
summary.append(['Pic mémoire backend observé',*[f'{fmt(maxmem[d],0)} Mio' for d in ['vm','dk']]])
memory_note=("La somme RSS mesure les processus hôtes identifiés, avec possibles pages partagées ; elle ne représente pas la RAM allouée. "
"Le démarrage VM va de trois VM éteintes à l'API saine ; Docker inclut le démarrage de son moteur Linux puis des trois conteneurs. "
"Ces durées comprennent l'orchestration et la résolution des contrôles de santé. Le repos est relevé après campagne et redémarrage. "
"(1) Premier palier atteignant 90 % du meilleur débit moyen réussi : repère descriptif, pas un seuil de service acceptable.")
if not baseline['dk']['docker_engine_memory_included']:memory_note+=' * La RAM du moteur Linux Docker n\'a pas été accessible : la valeur Docker est partielle et ne permet pas une comparaison totale de mémoire.'
detail=[['Déploiement','u.','Débit r1 / r2','p95 r1 / r2 (s)','Erreurs r1 / r2 (%)']]
for d in ['vm','dk']:
    for n in LEVELS:
        a,b=[data[d,n,r]['stats'] for r in [1,2]]
        detail.append([d.upper(),str(n),f"{fmt(a['throughput_rps'])} / {fmt(b['throughput_rps'])}",f"{fmt(a['p95_ms']/1000)} / {fmt(b['p95_ms']/1000)}",f"{fmt(a['error_pct'],1)} / {fmt(b['error_pct'],1)}"])
repeattext='Écart relatif = |r1 - r2| / moyenne × 100, calculé séparément sur le débit et le p95. '
repeattext+=('Dépassement du seuil de 10 % : '+', '.join(unstable)+'. Ces paliers restent publiés ; aucun meilleur essai n\'est sélectionné pour masquer la variation.') if unstable else 'Tous les paliers restent sous 10 % pour ces deux indicateurs.'
q1=f"Le meilleur débit sans erreur observé vaut {fmt(avg('vm',best['vm'],'successful_rps'))} req/s en VM et {fmt(avg('dk',best['dk'],'successful_rps'))} req/s sous Docker, aux charges indiquées page 1. À 10 utilisateurs, le p95 moyen est respectivement {fmt(avg('vm',10,'p95_ms')/1000)} s et {fmt(avg('dk',10,'p95_ms')/1000)} s. Ces moyennes décrivent deux essais ; ce ne sont pas des garanties de capacité durable."
q2="Les VM exécutent trois systèmes invités, tandis que les conteneurs partagent le noyau de la VM Linux de Docker Desktop. Le coût de l'ordonnancement et du réseau diffère. Les versions de Python (VM 3.12 / Docker 3.14), MySQL (8.0 / 8.4) et Nginx diffèrent également : les résultats comparent ces installations concrètes, sans isoler l'effet de la virtualisation."
evidence=[]
for d in ['vm','dk']:
    peak=max(data[d,n,r]['server']['services']['backend'].get('cpu_percent_mean',0) for n in LEVELS for r in [1,2])
    dbpeak=max(data[d,n,r]['server']['services']['db'].get('cpu_percent_mean',0) for n in LEVELS for r in [1,2])
    conn=max(data[d,n,r]['server'].get('Threads_connected_max') or 0 for n in LEVELS for r in [1,2])
    logs='\n'.join(p.read_text(encoding='utf-8',errors='replace') for p in (F/'etapes').glob(f'{d}-*-backend.txt'))
    pool='Les journaux confirment un pool SQLAlchemy de 5 + 10 connexions épuisé.' if 'QueuePool limit of size 5 overflow 10 reached' in logs else 'Aucune preuve de cette erreur de pool n\'a été trouvée dans les journaux collectés.'
    evidence.append(f"{d.upper()} : CPU moyen backend jusqu'à {fmt(peak,1)} % d'un cœur, contre {fmt(dbpeak,1)} % pour MySQL ; maximum {conn} connexions, surveillance comprise. {pool}")
q3=' '.join(evidence)+" Le pool est une limite applicative : cela ne prouve pas la saturation du moteur MySQL. Les courbes et les métriques par palier permettent de distinguer le ralentissement préalable de l'échec à forte charge."
if list((F/'etapes').glob('dk-recovery-*.json')):q3+=' Après la première surcharge Docker, le backend était unhealthy sans OOM ; un redémarrage hors mesure a précédé la réinitialisation de la série suivante.'
q4="Deux répétitions de 60 s ne couvrent ni l'endurance ni la disponibilité, les pannes ou une distribution multi-hôtes. Le poste héberge aussi l'injecteur ; les tâches de fond, caches et températures ne sont pas parfaitement contrôlés. Les temporisations client plafonnent les latences d'échec autour de 30 s. Les versions et les modalités de quotas/swap diffèrent. Les anciennes mesures sur le PC de Rémi restent historiques et sont exclues de cette comparaison."
gui_complete=all((F/'captures'/n).exists() for n in ['validation-positive.png','validation-negative.png','gui-positif.xml','gui-negatif.xml'])
status=("Validation GUI réalisée manuellement par l'utilisateur le 26 octobre 2026. Les captures et relevés montrent HTTP 200 pour la connexion et la consultation nominales, puis HTTP 401 et des assertions échouées avec le mot de passe incorrect. Les preuves sont conservées dans captures/." if gui_complete else "Les captures GUI positif et négatif restent à fournir ; les contrôles CLI ne les remplacent pas.")

source="Traçabilité : configuration.json (empreintes), PROTOCOLE.md, etapes/*-resultat.json, *-serveur.jsonl et *-backend.txt, calibration/, baseline-vm.json et baseline-dk.json. Les CSV bruts vm/dk portant l'identifiant "+ID+" sont dans bruts/charge ; l'étalonnage est dans bruts/etalonnage. Les données anciennes restent inchangées."

styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyFR',fontName='Helvetica',fontSize=9,leading=12,spaceAfter=8));styles.add(ParagraphStyle(name='SmallFR',fontSize=7.5,leading=10,spaceAfter=5))
story=[]
def p(text,style='BodyFR'):story.append(Paragraph(escape(text),styles[style]))
def title(text):story.append(Paragraph(escape(text),styles['Heading1']))
def table(rows,widths):
    rr=[[Paragraph(escape(str(c)),styles['SmallFR']) for c in row] for row in rows]
    t=Table(rr,colWidths=widths,repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf6')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#2463a0')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f7fa')]),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.append(t);story.append(Spacer(1,8))
title('MyHike - Comparaison VM / Docker')
p('Campagne réelle du '+DATE+' | Akrem SOUSSI et Rémi CORTIAL','SmallFR')
p(protocol);p(scenario);table(summary,[230,140,140]);p(memory_note,'SmallFR');p(caltext)
story.append(PageBreak());title('Courbes des deux répétitions')
for name in ['debit','latence','erreurs']:story.append(Image(str(F/'graphiques'/f'{name}.png'),width=510,height=152.4));story.append(Spacer(1,9))
p("Le débit total inclut les requêtes échouées. À forte charge, il faut lire simultanément le taux d'erreur ; le p95 des échecs reflète souvent le délai d'attente client.",'SmallFR')
story.append(PageBreak());title('Résultats et répétabilité');table(detail,[66,26,135,135,148]);p(repeattext);p("Les moyennes de la synthèse sont des moyennes des deux statistiques par essai, pas des percentiles recalculés sur un mélange de séries. Le détail complet, y compris les requêtes réussies par seconde, est fourni dans synthese.csv.")
p(status);p(source,'SmallFR')
story.append(PageBreak());title('Interprétation et limites')
for heading,text in [('1. De combien les déploiements diffèrent-ils ?',q1),('2. Quelles propriétés peuvent expliquer l\'écart ?',q2),('3. Quel composant limite le service ?',q3),('4. Que ne démontrent pas ces mesures ?',q4)]:story.append(Paragraph(escape(heading),styles['Heading2']));p(text)
p("Conclusion méthodologique : les paliers instables sont explicitement signalés. Le critère de répétabilité n'est pas satisfait à tous les paliers ; les résultats ne sont pas présentés comme une validation complète de toutes les exigences.",'SmallFR')
def footer(c,doc):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(42,24,'MyHike | Mesures du '+DATE);c.drawRightString(A4[0]-42,24,str(doc.page))
pdf=OUT/'rapport-comparaison.pdf'
SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=36,bottomMargin=38).build(story,onFirstPage=footer,onLaterPages=footer)
def mdtable(table):return '\n'.join('| '+' | '.join(row)+' |' for row in [table[0],['---']*len(table[0]),*table[1:]])
md='# MyHike - Rapport de comparaison VM / Docker\n\n'+DATE+' - mesures réelles\n\n## Protocole\n\n'+protocol+'\n\n'+scenario+'\n\n## Synthèse\n\n'+mdtable(summary)+'\n\n'+memory_note+'\n\n## Étalonnage\n\n'+caltext+'\n\n## Résultats\n\n'+mdtable(detail)+'\n\n'+repeattext
for name in ['debit','latence','erreurs']:md+=f'\n\n![{name}](../graphiques/{name}.png)'
for heading,text in [('Écarts chiffrés',q1),('Explications',q2),('Composant limitant',q3),('Limites',q4),('Validation et traçabilité',status+' '+source)]:md+='\n\n## '+heading+'\n\n'+text
(OUT/'rapport-comparaison.md').write_text(md+'\n',encoding='utf-8')
config=load(F/'configuration.json');config.update(completion='measurements_and_gui_complete' if gui_complete else 'measurements_complete_gui_captures_pending',completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),unstable_loads=unstable,repeatability_all_loads_under_10_percent=not unstable,gui_captures_complete=gui_complete,measured_load_runs=24)
(F/'configuration.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
print(pdf);print('Unstable:',unstable)
