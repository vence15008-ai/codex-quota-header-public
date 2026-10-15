// Isolate the mock from the real Codex debug port.
process.env.CODEX_QUOTA_CDP_PORT = '19341';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {trustedTarget, trustedSocket} = require('../cdp_bridge.cjs');
test('Only local renderer websocket endpoints', () => {
  assert.doesNotThrow(() => trustedSocket('ws://127.0.0.1:19341/devtools/page/example'));
  assert.throws(() => trustedSocket('ws://example.com:9222/page'));
  assert.throws(() => trustedSocket('ws://127.0.0.1:9999/page'));
  assert.throws(() => trustedSocket('wss://127.0.0.1:9222/page'));
  for (const address of ['ws://user:pass@127.0.0.1:19341/devtools/page/x',
    'ws://127.0.0.1:19341/devtools/browser/x','ws://127.0.0.1:19341/devtools/page/x?token=secret']) {
    assert.throws(() => trustedSocket(address));
  }
});
test('Ignore embedded external browser pages and background workers', () => {
  const target = url => ({url,type:'page',webSocketDebuggerUrl:'ws://127.0.0.1:9222/page'});
  assert.equal(trustedTarget(target('app://-/index.html')),true);
  assert.equal(trustedTarget(target('https://chatgpt.com/')),true);
  assert.equal(trustedTarget(target('https://github.com/')),false);
  assert.equal(trustedTarget({...target('app://-/index.html'),type:'worker'}),false);
  assert.equal(trustedTarget(null),false);
});
test('Invalid port configuration fails before any connection', () => {
  const {spawnSync} = require('node:child_process');
  const path = require('node:path');
  for (const port of ['0','NaN','9222.5','65536']) {
    const result = spawnSync(process.execPath, ['-e', 'require("./cdp_bridge.cjs")'], {
      cwd:path.join(__dirname,'..'), env:{...process.env,CODEX_QUOTA_CDP_PORT:port}, encoding:'utf8',windowsHide:true
    });
    assert.notEqual(result.status,0);
    assert.match(result.stderr,/Invalid CDP port/);
  }
});
test('Native WebSocket transport speaks CDP and correlates replies', async t => {
  const net = require('node:net');
  const crypto = require('node:crypto');
  const {CDP} = require('../cdp_bridge.cjs');
  const sockets = new Set();
  const server = net.createServer(socket => {
    sockets.add(socket);
    let buffer = Buffer.alloc(0), upgraded = false;
    socket.on('data', data => {
      buffer = Buffer.concat([buffer,data]);
      if (!upgraded) {
        const end = buffer.indexOf('\r\n\r\n');
        if (end < 0) return;
        const key = buffer.toString('utf8',0,end).match(/Sec-WebSocket-Key:\s*(.+)/i)[1].trim();
        const accept = crypto.createHash('sha1').update(key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');
        socket.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: '+accept+'\r\n\r\n');
        buffer = buffer.subarray(end+4); upgraded = true;
      }
      if (buffer.length < 2) return;
      const opcode = buffer[0]&15;
      if (opcode===8) {socket.end(Buffer.from([0x88,0]));return;}
      let length = buffer[1]&127, offset = 2;
      if (length===126) {if(buffer.length<4)return;length=buffer.readUInt16BE(2);offset=4;}
      if (buffer.length<offset+4+length)return;
      const mask=buffer.subarray(offset,offset+4), body=Buffer.from(buffer.subarray(offset+4,offset+4+length));
      for(let i=0;i<body.length;i++)body[i]^=mask[i%4];
      buffer=buffer.subarray(offset+4+length);
      const request=JSON.parse(body.toString());
      assert.equal(request.method,'Runtime.evaluate');
      const reply=Buffer.from(JSON.stringify({id:request.id,result:{result:{value:{mounted:true}}}}));
      socket.write(Buffer.concat([Buffer.from([0x81,reply.length]),reply]));
    });
  });
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(19341,'127.0.0.1',resolve);});
  t.after(()=>{for(const socket of sockets)socket.destroy();server.close();});
  const client = new CDP('ws://127.0.0.1:19341/devtools/page/mock');
  assert.deepEqual(await client.evaluate('({mounted:true})'),{mounted:true});
  client.close();
});
