#!/usr/bin/env python3
import json, os, signal, subprocess, threading, time
from pathlib import Path
from flask import Flask, jsonify, request
import requests
HOME_URL=os.getenv('SMARTTV_HOME','http://127.0.0.1:8765')
PROFILE=str(Path.home()/'.local/share/smarttv/chromium-profile')
STATE={'online':True,'current_app':'Home','browser_running':False,'keyboard':False,'started':time.time()}
app=Flask(__name__); browser=None

def chromium_bin():
 for x in ('chromium','chromium-browser'):
  p=subprocess.run(['sh','-lc',f'command -v {x}'],capture_output=True,text=True).stdout.strip()
  if p:return p
 raise RuntimeError('Chromium not found')
def launch_browser():
 global browser
 Path(PROFILE).mkdir(parents=True,exist_ok=True)
 args=[chromium_bin(),'--kiosk','--noerrdialogs','--disable-session-crashed-bubble','--no-first-run','--password-store=basic','--user-data-dir='+PROFILE,'--remote-debugging-port=9222',HOME_URL]
 browser=subprocess.Popen(args,env=os.environ.copy());STATE['browser_running']=True;STATE['current_app']='Home'
def cdp(cmd,params=None):
 tabs=requests.get('http://127.0.0.1:9222/json',timeout=2).json(); page=next(x for x in tabs if x.get('type')=='page'); import websocket
 ws=websocket.create_connection(page['webSocketDebuggerUrl'],timeout=2); ws.send(json.dumps({'id':1,'method':cmd,'params':params or {}})); out=ws.recv();ws.close();return out
def navigate(url,name):
 # xdotool is dependable with Chromium under Xwayland and avoids a websocket dependency.
 subprocess.run(['xdotool','search','--onlyvisible','--class','chromium','windowactivate','--sync','key','ctrl+l','type','--delay','1',url,'key','Return'],check=False)
 STATE['current_app']=name
def key(k): subprocess.run(['xdotool','search','--onlyvisible','--class','chromium','windowactivate','--sync','key',k],check=False)
def keyboard(show=True):
 if show:
  subprocess.Popen(['onboard','--size=1280x360','--x=0','--y=720'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);STATE['keyboard']=True
 else:
  subprocess.run(['pkill','-f','onboard'],check=False);STATE['keyboard']=False
@app.get('/status')
def status(): return jsonify(STATE|{'uptime':int(time.time()-STATE['started'])})
@app.post('/open')
def open_(): d=request.get_json(force=True);navigate(d['url'],d.get('name','App'));return {'ok':True}
@app.post('/home')
def home(): navigate(HOME_URL,'Home');return {'ok':True}
@app.post('/back')
def back(): key('alt+Left');return {'ok':True}
@app.post('/refresh')
def refresh(): key('ctrl+r');return {'ok':True}
@app.post('/keyboard')
def kb(): keyboard(True);return {'ok':True}
@app.post('/hide-keyboard')
def hkb(): keyboard(False);return {'ok':True}
@app.post('/restart-browser')
def rb():
 global browser
 if browser: browser.terminate()
 launch_browser();return {'ok':True}
@app.post('/exit')
def exit_():
 global browser
 if browser: browser.terminate();STATE['browser_running']=False
 return {'ok':True}
@app.post('/reboot')
def reboot(): subprocess.Popen(['systemctl','reboot']);return {'ok':True}
@app.post('/shutdown')
def shutdown(): subprocess.Popen(['systemctl','poweroff']);return {'ok':True}

def overlay():
 import tkinter as tk
 root=tk.Tk();root.overrideredirect(True);root.attributes('-topmost',True);root.configure(bg='#080b11');sw,sh=root.winfo_screenwidth(),root.winfo_screenheight()
 def panel(top=True):
  w=tk.Toplevel(root);w.overrideredirect(True);w.attributes('-topmost',True);w.configure(bg='#111827');w.withdraw()
  cmds=[('Home',lambda:requests.post('http://127.0.0.1:8766/home')),('Back',lambda:requests.post('http://127.0.0.1:8766/back')),('Refresh',lambda:requests.post('http://127.0.0.1:8766/refresh'))] if top else [('Keyboard',lambda:requests.post('http://127.0.0.1:8766/keyboard')),('Hide',lambda:requests.post('http://127.0.0.1:8766/hide-keyboard'))]
  for text,cmd in cmds: tk.Button(w,text=text,command=cmd,bg='#1e293b',fg='white',activebackground='#334155',relief='flat',font=('Sans',13,'bold'),padx=14,pady=10).pack(side='left')
  w.update_idletasks();w.geometry(f'+{sw-w.winfo_reqwidth()-8}+{8 if top else sh-w.winfo_reqheight()-8}')
  w.bind('<Leave>',lambda e:w.withdraw());return w
 top=panel(True);bot=panel(False)
 root.geometry(f'3x3+{sw-3}+0');root.bind('<Enter>',lambda e:top.deiconify())
 b=tk.Toplevel(root);b.overrideredirect(True);b.attributes('-topmost',True);b.configure(bg='#080b11');b.geometry(f'3x3+{sw-3}+{sh-3}');b.bind('<Enter>',lambda e:bot.deiconify())
 root.mainloop()
def main():
 threading.Thread(target=lambda:app.run(host='127.0.0.1',port=8766,debug=False,use_reloader=False),daemon=True).start()
 for _ in range(60):
  try: requests.get(HOME_URL+'/api/health',timeout=1);break
  except Exception: time.sleep(1)
 launch_browser();overlay()
if __name__=='__main__': main()
