import json,os,uuid,requests
from pathlib import Path
from urllib.parse import urlparse
from flask import Flask,request,jsonify,send_from_directory
D=Path(os.getenv('SMARTTV_DATA_DIR','/data'));D.mkdir(exist_ok=True);F=D/'apps.json';HOST=os.getenv('SMARTTV_HOST_AGENT','http://127.0.0.1:8766');GL=os.getenv('GLANCES_URL','http://127.0.0.1:61208').rstrip('/')
app=Flask(__name__,static_folder='static',static_url_path='')
DEFAULT={'media':[
{'id':'youtube','name':'YouTube','url':'https://www.youtube.com','color':'#ff0033','icon':'▶','description':'Watch videos, subscriptions, Shorts, and live content.'},
{'id':'netflix','name':'Netflix','url':'https://www.netflix.com','color':'#e50914','icon':'N','description':'Browse movies, series, and saved titles.'},
{'id':'prime','name':'Prime Video','url':'https://www.primevideo.com','color':'#00a8e1','icon':'P','description':'Open Prime Video movies, shows, and channels.'},
{'id':'appletv','name':'Apple TV','url':'https://tv.apple.com','color':'#e5e7eb','icon':'TV','description':'Watch Apple Originals, movies, and your library.'},
{'id':'applemusic','name':'Apple Music','url':'https://music.apple.com','color':'#fa2d48','icon':'♫','description':'Listen to albums, playlists, and radio.'},
{'id':'twitch','name':'Twitch','url':'https://www.twitch.tv','color':'#9146ff','icon':'T','description':'Watch live streams and followed creators.'}],
'dashboard':[
{'id':'homeassistant','name':'Home Assistant','url':'http://10.0.0.109:8123','color':'#18a5e3','icon':'⌂','description':'Control devices, scenes, dashboards, and automations.'},
{'id':'pihole','name':'Pi-hole','url':'http://10.0.0.109/admin','color':'#ef4444','icon':'◉','description':'Monitor DNS requests and network-wide blocking.'},
{'id':'portainer','name':'Portainer','url':'https://10.0.0.109:9443','color':'#13bef9','icon':'▣','description':'View and manage Docker containers and stacks.'},
{'id':'glances','name':'Glances','url':'http://10.0.0.109:61208','color':'#7cb342','icon':'G','description':'Monitor Raspberry Pi performance and system health.'}]}
def load():
 if not F.exists(): F.write_text(json.dumps(DEFAULT,indent=2))
 x=json.loads(F.read_text())
 for m in x:
  for a in x[m]: a.setdefault('description','Open this application in SmartTV.')
 return x
def save(x):
 t=F.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2));t.replace(F)
def okurl(u):
 p=urlparse(u);return p.scheme in ('http','https') and bool(p.netloc)
def hp(path,data=None):
 try:
  z=requests.post(HOST+path,json=data or {},timeout=5);return z.json(),z.status_code
 except Exception as e:return {'ok':False,'error':str(e)},503
@app.get('/')
def index():return send_from_directory(app.static_folder,'index.html')
@app.get('/api/health')
def health():return {'ok':True,'service':'smarttv-backend','version':'1.0.2'}
@app.get('/api/apps')
def ga():return jsonify(load())
@app.post('/api/apps')
def aa():
 d=request.get_json();m=d.get('mode','media');n=str(d.get('name','')).strip();u=str(d.get('url','')).strip()
 if m not in DEFAULT or not n or not okurl(u):return {'error':'A name and valid HTTP(S) URL are required.'},400
 x=load();a={'id':'custom-'+uuid.uuid4().hex[:9],'name':n[:50],'url':u,'color':d.get('color','#0ea5e9'),'icon':n[0].upper(),'description':str(d.get('description','Open this application in SmartTV.'))[:180]};x[m].append(a);save(x);return a,201
@app.delete('/api/apps/<i>')
def da(i):
 x=load()
 for m in x:
  if any(a['id']==i for a in x[m]):x[m]=[a for a in x[m] if a['id']!=i];save(x);return {'ok':True}
 return {'error':'Not found'},404
@app.post('/api/open')
def op():
 d=request.get_json();return hp('/open',{'url':d['url'],'name':d.get('name','App')})
@app.post('/api/control/<a>')
def ctl(a):return hp('/'+a)
@app.get('/api/network')
def net():
 try:z=requests.get(HOST+'/network',timeout=2);return z.json(),z.status_code
 except Exception as e:return {'error':str(e)},503
@app.get('/api/stats')
def stats():
 out={'available':False}
 for key,ep in {'cpu':'cpu','mem':'mem','processcount':'processcount','sensors':'sensors','containers':'containers'}.items():
  try:z=requests.get(f'{GL}/api/4/{ep}',timeout=2);out[key]=z.json();out['available']=True
  except:pass
 try:z=requests.get(HOST+'/status',timeout=2);out['smarttv']=z.json()
 except:out['smarttv']={'online':False}
 return jsonify(out)
