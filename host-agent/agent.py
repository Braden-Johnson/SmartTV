#!/usr/bin/env python3
import json,os,subprocess,threading,time,queue,requests
from pathlib import Path
from flask import Flask,request,jsonify
import websocket
HOME=os.getenv('SMARTTV_HOME','http://127.0.0.1:8765');PROFILE=str(Path.home()/'.local/share/smarttv/chromium-profile');STATE={'online':True,'current_app':'Home','browser_running':False,'keyboard':False,'started':time.time()};Q=queue.Queue();app=Flask(__name__);browser=None

def chrome():
 for x in ('chromium','chromium-browser'):
  p=subprocess.run(['sh','-lc',f'command -v {x}'],capture_output=True,text=True).stdout.strip()
  if p:return p
 raise RuntimeError('Chromium not found')
def launch():
 global browser
 Path(PROFILE).mkdir(parents=True,exist_ok=True);browser=subprocess.Popen([chrome(),'--kiosk','--noerrdialogs','--disable-session-crashed-bubble','--no-first-run','--password-store=basic','--user-data-dir='+PROFILE,'--remote-debugging-port=9222','--remote-allow-origins=*','--ozone-platform=x11',HOME]);STATE.update(browser_running=True,current_app='Home')
def cdp(method,params=None):
 tabs=requests.get('http://127.0.0.1:9222/json',timeout=2).json();page=next(x for x in tabs if x.get('type')=='page');w=websocket.create_connection(page['webSocketDebuggerUrl'],timeout=3,origin='http://127.0.0.1:9222');w.send(json.dumps({'id':1,'method':method,'params':params or {}}));out=json.loads(w.recv());w.close();return out
def nav(url,name):cdp('Page.navigate',{'url':url});STATE['current_app']=name
def remember():cdp('Runtime.evaluate',{'expression':"window.__smarttvInput=document.activeElement;if(window.__smarttvInput)window.__smarttvInput.focus();true"})
def focus():cdp('Runtime.evaluate',{'expression':"if(window.__smarttvInput&&document.contains(window.__smarttvInput)){window.__smarttvInput.focus();true}else false"})
def text(v):focus();cdp('Input.insertText',{'text':v})
def key(k,code=None):focus();cdp('Input.dispatchKeyEvent',{'type':'keyDown','key':k,'code':code or k});cdp('Input.dispatchKeyEvent',{'type':'keyUp','key':k,'code':code or k})
@app.get('/status')
def status():return jsonify(STATE|{'uptime':int(time.time()-STATE['started'])})
@app.post('/open')
def op():d=request.get_json();nav(d['url'],d.get('name','App'));return {'ok':True}
@app.post('/home')
def home():nav(HOME,'Home');return {'ok':True}
@app.post('/back')
def back():cdp('Runtime.evaluate',{'expression':'history.back()'});return {'ok':True}
@app.post('/refresh')
def refresh():cdp('Page.reload',{});return {'ok':True}
@app.post('/keyboard')
def keyboard():
 try:remember()
 except:pass
 Q.put('show');return {'ok':True}
@app.post('/hide-keyboard')
def hide():Q.put('hide');return {'ok':True}
@app.post('/exit')
def ex():
 global browser
 if browser:browser.terminate()
 STATE['browser_running']=False;return {'ok':True}
@app.get('/network')
def net():
 def run(c):return subprocess.run(c,capture_output=True,text=True).stdout.strip()
 a=run(['ip','route','get','1.1.1.1']).split();i=a[a.index('dev')+1] if 'dev' in a else 'unknown';ip=a[a.index('src')+1] if 'src' in a else run(['hostname','-I']).split()[0];kind='Ethernet' if i.startswith(('eth','en')) else ('Wi-Fi' if i.startswith(('wl','wlan')) else i)
 return {'interface':i,'type':kind,'ip':ip,'ssid':run(['iwgetid','-r']) or None,'hostname':run(['hostname'])}
def ui():
 import tkinter as tk
 root=tk.Tk();root.overrideredirect(True);root.attributes('-topmost',True);root.configure(bg='#080b11');sw,sh=root.winfo_screenwidth(),root.winfo_screenheight()
 def panel(top=True):
  w=tk.Toplevel(root);w.overrideredirect(True);w.attributes('-topmost',True);w.configure(bg='#111827');w.withdraw();cmds=[('Home',lambda:requests.post('http://127.0.0.1:8766/home')),('Back',lambda:requests.post('http://127.0.0.1:8766/back')),('Refresh',lambda:requests.post('http://127.0.0.1:8766/refresh'))] if top else [('Keyboard',lambda:requests.post('http://127.0.0.1:8766/keyboard')),('Hide',lambda:requests.post('http://127.0.0.1:8766/hide-keyboard'))]
  for t,c in cmds:tk.Button(w,text=t,command=c,bg='#1e293b',fg='white',relief='flat',font=('Sans',13,'bold'),padx=16,pady=11).pack(side='left',padx=2,pady=2)
  w.update_idletasks();w.geometry(f'+{sw-w.winfo_reqwidth()}+{0 if top else sh-w.winfo_reqheight()}');timer={'id':None}
  def enter(e=None):
   if timer['id']:root.after_cancel(timer['id']);timer['id']=None
  def leave(e=None):timer['id']=root.after(1500,w.withdraw)
  w.bind('<Enter>',enter);w.bind('<Leave>',leave);return w
 top=panel(True);bot=panel(False);root.geometry(f'14x14+{sw-14}+0');root.bind('<Enter>',lambda e:(top.deiconify(),top.lift()));b=tk.Toplevel(root);b.overrideredirect(True);b.attributes('-topmost',True);b.geometry(f'14x14+{sw-14}+{sh-14}');b.bind('<Enter>',lambda e:(bot.deiconify(),bot.lift()))
 kb=tk.Toplevel(root);kb.overrideredirect(True);kb.attributes('-topmost',True);kb.configure(bg='#0b1220');kb.withdraw();upper={'on':False};pos={'top':False}
 def send(v):threading.Thread(target=lambda:text(v),daemon=True).start()
 def special(v):threading.Thread(target=lambda:key(v),daemon=True).start()
 def draw():
  for x in kb.winfo_children():x.destroy()
  rows=['1234567890','QWERTYUIOP','ASDFGHJKL','ZXCVBNM']
  for ri,row in enumerate(rows):
   f=tk.Frame(kb,bg='#0b1220');f.pack(pady=3)
   for ch in row:tk.Button(f,text=ch,command=lambda c=ch:send(c if upper['on'] else c.lower()),width=4,height=1,bg='#1e293b',fg='white',activebackground='#334155',relief='flat',font=('Sans',15,'bold')).pack(side='left',padx=3)
  f=tk.Frame(kb,bg='#0b1220');f.pack(pady=4)
  for label,cmd,width in [('Shift',lambda:(upper.update(on=not upper['on']),draw()),7),('@',lambda:send('@'),4),('Space',lambda:send(' '),18),('.com',lambda:send('.com'),7),('⌫',lambda:special('Backspace'),6),('Enter',lambda:special('Enter'),7),('Move',lambda:(pos.update(top=not pos['top']),place()),6),('Done',lambda:(kb.withdraw(),STATE.update(keyboard=False)),6)]:tk.Button(f,text=label,command=cmd,width=width,bg='#263449',fg='white',relief='flat',font=('Sans',13,'bold'),pady=9).pack(side='left',padx=3)
  place()
 def place():kb.update_idletasks();kb.geometry(f'{min(sw-40,1260)}x{kb.winfo_reqheight()+16}+{max(0,(sw-min(sw-40,1260))//2)}+{12 if pos["top"] else sh-kb.winfo_reqheight()-28}')
 draw()
 def poll():
  try:
   while True:
    x=Q.get_nowait()
    if x=='show':kb.deiconify();kb.lift();STATE['keyboard']=True
    else:kb.withdraw();STATE['keyboard']=False
  except queue.Empty:pass
  root.after(100,poll)
 poll();root.mainloop()
def main():
 threading.Thread(target=lambda:app.run(host='127.0.0.1',port=8766,debug=False,use_reloader=False),daemon=True).start()
 for _ in range(60):
  try:requests.get(HOME+'/api/health',timeout=1);break
  except:time.sleep(1)
 launch();ui()
if __name__=='__main__':main()
