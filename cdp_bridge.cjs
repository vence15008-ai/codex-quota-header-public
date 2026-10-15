/* Node >=22 native WebSocket; no third-party packages and no HTTP quota server. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const {spawn} = require('node:child_process');
const readline = require('node:readline');
const PORT = Number(process.env.CODEX_QUOTA_CDP_PORT || 9222);
if (!Number.isInteger(PORT) || PORT < 1024 || PORT > 65535) throw new Error('Invalid CDP port (1024..65535 required)');
const KEY = '__codexQuotaHeaderV1';
let ui = fs.readFileSync(path.join(__dirname, 'header.js'), 'utf8');
let uiModified = fs.statSync(path.join(__dirname,'header.js')).mtimeMs;

function trustedTarget(target) {
  if (!target || target.type !== 'page' || !target.webSocketDebuggerUrl) return false;
  try {
    const u = new URL(target.url);
    return ['app:', 'codex:', 'chatgpt:', 'file:'].includes(u.protocol) ||
      (u.protocol === 'https:' && u.hostname === 'chatgpt.com');
  } catch { return false; }
}
function trustedSocket(address) {
  const u = new URL(address);
  if (u.protocol !== 'ws:' || !['127.0.0.1','localhost','[::1]'].includes(u.hostname) ||
      Number(u.port) !== PORT || u.username || u.password || u.search || u.hash ||
      !/^\/devtools\/page\/[\w-]+$/.test(u.pathname)) throw new Error('Refusing untrusted CDP endpoint');
  return u;
}

class CDP {
  constructor(address) {
    trustedSocket(address);
    this.pending = new Map();
    this.id = 0;
    this.ws = new WebSocket(address);
    this.open = new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {this.close(); reject(new Error('CDP connection timeout'));}, 5000);
      this.ws.addEventListener('open', () => {clearTimeout(timeout); resolve();}, {once:true});
      this.ws.addEventListener('error', () => {clearTimeout(timeout); reject(new Error('CDP connection failed'));}, {once:true});
    });
    this.ws.addEventListener('message', event => {
      let message;
      try {message = JSON.parse(String(event.data));} catch {return;}
      const request = this.pending.get(message.id);
      if (!request) return;
      clearTimeout(request.timeout); this.pending.delete(message.id);
      if (message.error) request.reject(new Error(message.error.message));
      else request.resolve(message.result);
    });
    this.ws.addEventListener('close', () => {
      for (const request of this.pending.values()) {
        clearTimeout(request.timeout); request.reject(new Error('CDP disconnected'));
      }
      this.pending.clear();
    });
    // Observe open rejection even before the first call.
    this.open.catch(() => {});
  }
  async call(method,params) {
    await this.open;
    const id = ++this.id;
    const result = await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {this.pending.delete(id); reject(new Error('CDP request timeout'));}, 5000);
      this.pending.set(id, {resolve, reject, timeout});
      try {this.ws.send(JSON.stringify({id,method,params}));}
      catch (error) {clearTimeout(timeout); this.pending.delete(id); reject(error);}
    });
    return result;
  }
  async evaluate(expression) {
    const result=await this.call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true,userGesture:false});
    if (result.exceptionDetails) throw new Error('Quota UI evaluation failed');
    return result.result?.value;
  }
  close() {try {this.ws.close();} catch {}}
}

async function targets() {
  const response = await fetch(`http://127.0.0.1:${PORT}/json/list`, {signal:AbortSignal.timeout(3000),redirect:'error'});
  if (!response.ok) throw new Error('CDP target discovery failed');
  const result = await response.json();
  if (!Array.isArray(result)) throw new Error('Invalid CDP target list');
  return result.filter(trustedTarget);
}

async function main() {
  const removing = process.argv.includes('--remove');
  let state = {view:null, updatedAt:null, loading:true, error:null};
  let revision = 0;
  let stopping = false;
  let child;
  const sessions = new Map();
  let lastStatus = '';
  function status(message) {
    if (message !== lastStatus) {console.log(message); lastStatus = message;}
  }
  if (!removing) {
    const python = process.env.CODEX_QUOTA_PYTHON;
    if (!python) throw new Error('CODEX_QUOTA_PYTHON is required');
    child = spawn(python, ['-u', path.join(__dirname,'quota_feed.py')], {
      cwd:__dirname, windowsHide:true, stdio:['pipe','pipe','pipe'],
      env:{...process.env, PYTHONIOENCODING:'utf-8'}
    });
    // Drain stderr, but never persist arbitrary child output (could contain paths/account data).
    child.stderr.resume();
    child.stdin.on('error', () => {if (!stopping) {state = {...state, loading:false,error:'额度读取进程连接中断，请重启组件'}; revision++;}});
    readline.createInterface({input:child.stdout}).on('line', line => {
      try {state = JSON.parse(line); revision++;} catch {}
    });
    child.on('error', () => {state = {...state, loading:false,error:'额度读取进程启动失败'}; revision++;});
    child.on('exit', () => {if (!stopping) {state = {...state,loading:false,error:'额度读取进程退出，请重新启动内嵌组件'}; revision++;}});
  }
  async function tick() {
    const modified=fs.statSync(path.join(__dirname,'header.js')).mtimeMs;
    if(modified!==uiModified) {ui=fs.readFileSync(path.join(__dirname,'header.js'),'utf8');uiModified=modified;revision++;}
    const found = await targets();
    const ids = new Set(found.map(t => t.id));
    for (const [id, entry] of sessions) {
      if (!ids.has(id)) {entry.cdp.close(); sessions.delete(id);}
    }
    let mounted = 0;
    for (const target of found) {
      let entry = sessions.get(target.id);
      try {
        if (!entry) {entry = {cdp:new CDP(target.webSocketDebuggerUrl), revision:-1}; sessions.set(target.id,entry);}
        if (removing) {await entry.cdp.evaluate(`window.${KEY}?.remove()`); continue;}
        const result = entry.revision !== revision
          ? await entry.cdp.evaluate(`(${ui})(${JSON.stringify(state)})`)
          : await entry.cdp.evaluate(`window.${KEY}?.poll() ?? null`);
        if (!result) {entry.revision = -1; continue;}
        entry.revision = revision;
        if (result.mounted) mounted++;
        if (result.refreshRequested && child?.stdin.writable) child.stdin.write('{"command":"refresh"}\n');
      } catch (error) {entry?.cdp.close(); sessions.delete(target.id); if (removing) throw error;}
    }
    status(mounted && state.view?.week && !state.error ? `Quota header mounted in ${mounted} renderer(s)` : 'Waiting for the native Codex header and live quota');
  }
  function stop() {
    stopping = true;
    if (child?.stdin.writable) child.stdin.end('{"command":"stop"}\n');
    for (const entry of sessions.values()) entry.cdp.close();
    // If app-server is stuck, the detached worker cleanup is bounded.
    setTimeout(() => {child?.kill(); process.exit(process.exitCode || 0);}, 2500).unref();
  }
  process.on('SIGINT',stop); process.on('SIGTERM',stop);
  do {
    if (!removing && fs.existsSync(path.join(__dirname,'runtime','stop'))) break;
    try {await tick();} catch (error) {
      if (removing) {process.exitCode=1; console.error('Could not remove quota header: ' + error.message); break;}
      status('Waiting for Codex on localhost:' + PORT);
    }
    if (removing) break;
    await new Promise(resolve => setTimeout(resolve,2000));
  } while (!stopping);
  stop();
}

module.exports = {trustedTarget, trustedSocket, CDP, targets, PORT};
if (require.main === module) main().catch(() => {console.error('Quota header helper failed to start'); process.exitCode = 1;});
