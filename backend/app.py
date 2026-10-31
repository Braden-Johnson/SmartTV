import json, os, socket, time, uuid
from pathlib import Path
from urllib.parse import urlparse
import requests
from flask import Flask, jsonify, request, send_from_directory

BASE=Path(__file__).resolve().parent
DATA=Path(os.getenv('SMARTTV_DATA_DIR', BASE/'data'))
DATA.mkdir(parents=True, exist_ok=True)
APPS_FILE=DATA/'apps.json'
HOST=os.getenv('SMARTTV_HOST_AGENT','http://127.0.0.1:8766')
GLANCES=os.getenv('GLANCES_URL','http://127.0.0.1:61208').rstrip('/')
app=Flask(__name__, static_folder='static', static_url_path='')
DEFAULT_APPS={
 'media':[
  {'id':'netflix','name':'Netflix','url':'https://www.netflix.com','color':'#e50914','icon':'N'},
  {'id':'prime','name':'Prime Video','url':'https://www.primevideo.com','color':'#00a8e1','icon':'P'},
  {'id':'youtube','name':'YouTube','url':'https://www.youtube.com/tv','color':'#ff0000','icon':'▶'},
  {'id':'appletv','name':'Apple TV','url':'https://tv.apple.com','color':'#f5f5f7','icon':'TV'},
  {'id':'applemusic','name':'Apple Music','url':'https://music.apple.com','color':'#fa243c','icon':'♫'},
  {'id':'twitch','name':'Twitch','url':'https://www.twitch.tv','color':'#9146ff','icon':'T'},
  {'id':'plex','name':'Plex','url':'http://10.0.0.109:32400/web','color':'#e5a00d','icon':'X'}],
 'dashboard':[
  {'id':'homeassistant','name':'Home Assistant','url':'http://10.0.0.109:8123','color':'#03a9f4','icon':'⌂'},
  {'id':'pihole','name':'Pi-hole','url':'http://10.0.0.109/admin','color':'#f05252','icon':'◉'},
  {'id':'portainer','name':'Portainer','url':'https://10.0.0.109:9443','color':'#13bef9','icon':'▣'},
  {'id':'glances','name':'Glances','url':'http://10.0.0.109:61208','color':'#7cb342','icon':'G'}]
}
def load_apps():
 if not APPS_FILE.exists(): save_apps(DEFAULT_APPS)
 try: return json.loads(APPS_FILE.read_text())
 except Exception: return DEFAULT_APPS
def save_apps(data):
 tmp=APPS_FILE.with_suffix('.tmp'); tmp.write_text(json.dumps(data,indent=2)); tmp.replace(APPS_FILE)
def valid_url(url):
 try: return urlparse(url).scheme in ('http','https') and bool(urlparse(url).netloc)
 except Exception: return False
def host_post(path, payload=None):
 try:
  r=requests.post(HOST+path,json=payload or {},timeout=4); return r.json(),r.status_code
 except Exception as e: return {'ok':False,'error':str(e)},503
@app.get('/')
def index(): return send_from_directory(app.static_folder,'index.html')
@app.get('/api/health')
def health(): return {'ok':True,'service':'smarttv-backend','version':'1.0.0'}
@app.get('/api/apps')
def apps_get(): return jsonify(load_apps())
@app.post('/api/apps')
def apps_add():
 d=request.get_json(force=True); mode=d.get('mode','media'); name=str(d.get('name','')).strip(); url=str(d.get('url','')).strip()
 if mode not in ('media','dashboard') or not name or not valid_url(url): return {'ok':False,'error':'Valid name, mode, and http(s) URL required'},400
 data=load_apps(); item={'id':'custom-'+uuid.uuid4().hex[:10],'name':name[:50],'url':url,'color':d.get('color','#0ea5e9'),'icon':name[:1].upper()}; data[mode].append(item); save_apps(data); return item,201
@app.put('/api/apps/<item_id>')
def apps_edit(item_id):
 d=request.get_json(force=True); data=load_apps()
 for mode in data:
  for item in data[mode]:
   if item['id']==item_id:
    if 'name' in d: item['name']=str(d['name']).strip()[:50]
    if 'url' in d and valid_url(str(d['url'])): item['url']=str(d['url'])
    if 'color' in d: item['color']=str(d['color'])
    save_apps(data); return item
 return {'ok':False,'error':'Not found'},404
@app.delete('/api/apps/<item_id>')
def apps_delete(item_id):
 data=load_apps()
 for mode in data:
  before=len(data[mode]); data[mode]=[x for x in data[mode] if x['id']!=item_id]
  if len(data[mode])<before: save_apps(data); return {'ok':True}
 return {'ok':False,'error':'Not found'},404
@app.post('/api/open')
def open_app():
 d=request.get_json(force=True); url=str(d.get('url',''))
 if not valid_url(url): return {'ok':False,'error':'Invalid URL'},400
 return host_post('/open',{'url':url,'name':d.get('name','App')})
@app.post('/api/control/<action>')
def control(action):
 if action not in ('home','back','refresh','keyboard','hide-keyboard','exit','restart-browser','reboot','shutdown'): return {'ok':False,'error':'Unknown action'},404
 return host_post('/'+action)
@app.get('/api/stats')
def stats():
 out={'available':False,'hostname':socket.gethostname(),'timestamp':time.time()}
 endpoints={'cpu':'cpu','mem':'mem','load':'load','processcount':'processcount','sensors':'sensors','fs':'fs','docker':'containers','network':'network'}
 for key,ep in endpoints.items():
  for ver in ('4','3'):
   try:
    r=requests.get(f'{GLANCES}/api/{ver}/{ep}',timeout=1.4)
    if r.ok: out[key]=r.json(); out['available']=True; out['api_version']=ver; break
   except Exception: pass
 try:
  r=requests.get(HOST+'/status',timeout=1.5); out['smarttv']=r.json() if r.ok else {'online':False}
 except Exception: out['smarttv']={'online':False}
 return jsonify(out)
@app.get('/api/update')
def update_status(): return {'version':'1.0.0','channel':'main','automatic':True}
