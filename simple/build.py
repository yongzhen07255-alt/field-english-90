import hashlib, html, json, pathlib, re, sys
from collections import Counter

HERE=pathlib.Path(__file__).resolve().parent
SITE=pathlib.Path(sys.argv[1]); dest=SITE/'course.json'
c=json.loads(dest.read_text(encoding='utf8'))
assert c['version']=='2.0.0', 'Use the original v2 release as the base'
words=[v for v in c['cards'] if v.get('active') and v['kind']=='word']
assert len(words)==346 and [v['en'] for v in words[286:289]]==['remote-access VPN','IPsec tunnel','encryption overhead']
def pair(s):
    a,b=map(str.strip,s.split('~')); assert a and b; return a,b
def rows(p):
    return [s.split('|') for s in p.read_text(encoding='utf8').splitlines() if s.strip()]
ex=[pair(r[1]) for r in rows(HERE/'word-examples.txt')];ex.insert(287,('Our branch uses an IPsec tunnel.','我们的分支使用 IPsec 隧道。'))
assert len(ex)==len(words)
for w,(a,b) in zip(words,ex):
    assert w['en'].lower() in a.lower() or w['en']=='reproduce a problem',(w['en'],a)
    w.update(contextEn=a,contextZh=b)
byid={v['id']:v for v in c['cards']}; bytext={(v['kind'],v['en'].lower()):v for v in c['cards'] if v.get('active')}
for v in c['cards']:
    if v['kind']!='word':v['active']=False
new_audio={}
def card(kind,ab,day,slot='',prompt=None):
    en,zh=ab
    v=bytext.get((kind,en.lower())) if kind=='phrase' else None
    if not v:
        key=f'{day}:{slot}:{en}' if kind=='task' else en.lower();ident='s3-'+kind[0]+hashlib.sha256(key.encode()).hexdigest()[:14]
        if ident in byid: v=byid[ident]
        else:
            v={'id':ident,'kind':kind,'en':en,'zh':zh,'sourceDays':[]};byid[ident]=v;c['cards'].append(v)
            if kind=='phrase':
                v['audio']='audio/simple/'+ident+'.mp3';new_audio[v['audio']]=en
    if kind=='phrase':bytext[kind,en.lower()]=v
    if not v.get('active'):v['sourceDays']=[]
    v.update(active=True,zh=zh);v['sourceDays']=sorted(set(v['sourceDays']+[day]));
    if prompt:v['prompt']=prompt
    return v['id']
records={int(r[0]):[pair(x) for x in r[1:]] for p in sorted(HERE.glob('days-*.txt')) for r in rows(p)}
ends={int(k):pair(v) for k,v in rows(HERE/'followups.txt')}
assert sorted(records)==sorted(ends)==list(range(1,91)); assert all(len(v)==7 for v in records.values())
records[2][1]=('It dropped at noon yesterday.','昨天中午十二点断了。')
ends[70]=(ends[70][0],'我会加上线路切换后的支付检查。')
records[34][5]=('Please keep our family photos out of the picture.','请别把我们的家庭照片拍进去。')
records[55][4]=('Can we meet indoors today instead?','今天可以改在室内见面吗？')
for d in c['days']:
    day=d['day']; a=records[day]; end=ends[day]; idx=[card('phrase',p,day) for p in a[:6]]
    d['scene']='模拟访谈｜'+d['topic']+'。客户的第一条线索：'+a[1][1];d['goal']='先问「'+a[0][1]+'」听完再追问。每句只讲一件事，可以加上时间或地点。'
    d['dialogue']=[{'speaker':'我' if i%2==0 else '客户','id':k} for i,k in enumerate(idx)]
    extra=card('phrase',a[6],day)
    if d['review_only']:
        previous=[p for p in c['days'] if p['week']==d['week'] and p['day']<day]
        d['phraseIds']=[p['phraseIds'][j%4] for j,p in enumerate(previous[-4:])];assert len(set(d['phraseIds']))==4
        for k in d['phraseIds']:byid[k]['sourceDays']=sorted(set(byid[k]['sourceDays']+[day]))
    else:d['phraseIds']=[idx[0],idx[2],idx[4],extra]
    tasks=[('访谈人｜围绕「'+d['topic']+'」分三次开口。每说一句，停下来等客户回答；再换一处项目细节重练。',[a[i] for i in (0,2,4)]),('客户｜分别接住刚才三句话。第一遍用场景里的信息回答，第二遍换成自己项目的事实。',[a[i] for i in (1,3,5)]),('互换角色｜接着说：「'+a[6][1]+'」先演双方，再换一个人、时间或地点重演。前两轮各练约45–60秒，这一轮也用同样时长。',[a[6],end])]
    d['taskIds']=[card('task',(' '.join(x[0] for x in lines),''.join(x[1] for x in lines)),day,str(j),prompt) for j,(prompt,lines) in enumerate(tasks)]
c.update(version='3.0.0',level='专业词汇 · 简单句');dest.write_text(json.dumps(c,ensure_ascii=False,separators=(',',':')),encoding='utf8')
changes={'app.js':{'实用中级 B1–B2':'客户访谈简句版','网络专业词库 · B1–B2':'五类网络产品专业词库','访谈英语 v2.0 · B1–B2':'访谈英语 v3.0 · 简句版','口头任务 · 连续说45–60秒':'口头任务 · 分角色练45–60秒','用今天的词句组织45–60秒回答：现状、影响、追问或下一步。':'先说一个短句，再加时间或地点。轮流问答，换一个细节重练。','三个任务各说45–60秒':'三个任务各练45–60秒，每次只说一个短句'},'sw.js':{'fbec289c0ed7':'simple3-20261120','version:\'2.0.0\'':'version:\'3.0.0\''},'update.html':{'正在更新到 v2.0':'正在更新到客户访谈简句版','if(version?.rangeAudio)':'if(version?.version===\'3.0.0\')'},'index.html':{'访谈英语 · 90天':'访谈英语 · 90天简句版'}}
for file,subs in changes.items():
    p=SITE/file;s=p.read_text(encoding='utf8');
    for x,y in subs.items():
        assert x in s,(file,x);s=s.replace(x,y)
    p.write_text(s,encoding='utf8')
# A compact, genuinely offline reader to keep in Files or Feishu.
e=html.escape
h=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>访谈英语 · 90天简句随身本</title><style>*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:auto;max-width:42rem;padding:1rem 1.25rem 4rem;background:#faf8f3;color:#18312e;font:16px/1.65 system-ui,sans-serif}h1{line-height:1.2}h2{color:#165d52;margin:0;font-size:1.4rem}h3{font-size:1rem;margin-top:1.4rem}b[lang]{display:block;line-height:1.42;font-size:1.12rem}small{color:#465d56}nav{display:flex;flex-wrap:wrap;gap:.32rem}nav a{min-width:2.4rem;text-align:center;background:#e7efea;border-radius:.4rem;padding:.32rem;text-decoration:none;color:#174f46}article{padding:2rem 0;border-bottom:1px solid #bccbc5}p{margin:.6rem 0}em{font-style:normal;color:#397166}summary{cursor:pointer}a{color:#176658}@media print{nav,.back{display:none}article{break-before:page}body{max-width:none}details>*{display:block}}</style><header id="top"><small>FIELD ENGLISH / 90 DAYS</small><h1>客户访谈英语<br>90天简句随身本</h1><p>一句只讲一件事。先说主语、动词和对象，再按需加时间或地点。问完停一下，把下一句话留给客户。</p><p><b>每天30分钟：</b>5分钟复习旧卡，8分钟背10个词并造句，8分钟跟读和替换4句，9分钟做角色问答。场景和数字均为模拟，可换成自己的项目。</p><p>这是离线文字本。需要听音、练卡或记进度，请打开<a href="https://yongzhen07255-alt.github.io/field-english-90/update.html">有声练习版</a>。</p></header><nav>']
h.extend(f'<a href="#d{i}">{i:02}</a>' for i in range(1,91));h.append('</nav>')
def line(p):return '<b lang="en">'+e(p[0])+'</b><small>'+e(p[1])+'</small>'
for d in c['days']:
    day=d['day']; h.append(f'<article id="d{day}"><small>DAY {day:02} / 90'+(' · 复习日' if d['review_only'] else '')+'</small><h2>'+e(d['topic'])+'</h2><p>'+e(d['scene'])+'</p><h3>01　词汇与例句</h3>')
    for k in d['wordIds']:
        w=byid[k];h.append('<p><b>'+e(w['en'])+' · '+e(w['zh'])+'</b><br>'+e(w['contextEn'])+'<br><small>'+e(w['contextZh'])+'</small></p>')
    h.append('<h3>02　四个核心句</h3>');h.extend('<p>'+line((byid[k]['en'],byid[k]['zh']))+'</p>' for k in d['phraseIds']);h.append('<h3>03　六句访谈</h3>');h.extend('<p><em>'+t['speaker']+'</em>'+line((byid[t['id']]['en'],byid[t['id']]['zh']))+'</p>' for t in d['dialogue']);h.append('<h3>04　开口三轮</h3>');
    for k in d['taskIds']:
        t=byid[k];h.append('<p>'+e(t['prompt'])+'</p><details><summary>看参考说法</summary>'+line((t['en'],t['zh']))+'</details>')
    h.append('<p class="back"><a href="#top">回到选课</a></p></article>')
(SITE/'pocket.html').write_text(''.join(h)+'</html>',encoding='utf8');(SITE.parent/'simple-audio.json').write_text(json.dumps(new_audio,ensure_ascii=False),encoding='utf8')
for d in c['days']:
    assert len(d['wordIds'])==10 and len(d['phraseIds'])==4 and len(d['dialogue'])==6 and len(d['taskIds'])==3
    assert all(byid[k]['active'] for k in d['wordIds']+d['phraseIds']+d['taskIds']+[z['id'] for z in d['dialogue']]);
for seq in records.values():
    for en,zh in seq:assert len(en.split())<=12 and not re.search(r'\b(although|because|unless|whether|whereas)\b',en,re.I),en
assert sum(p['minutes'] for p in c['plan'])==30
print('Built',len(c['days']),'lessons;',len(words),'word examples;',len(new_audio),'new recordings')
