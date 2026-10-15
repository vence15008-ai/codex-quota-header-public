// Hot-update this component only. Never restart Codex or open its debug port.
const fs=require('node:fs');
const path=require('node:path');
const {CDP,targets}=require('../cdp_bridge.cjs');
(async()=>{
  const source=fs.readFileSync(path.join(__dirname,'../header.js'),'utf8');
  const found=await targets();
  let count=0;
  for(const target of found){
    const client=new CDP(target.webSocketDebuggerUrl);
    try{
      const state=await client.evaluate('window.__codexQuotaHeaderV1?.state ?? null');
      if(!state)continue;
      const result=await client.evaluate(`(()=>{window.__codexQuotaHeaderV1?.remove();return (${source})(${JSON.stringify(state)});})()`);
      console.log(JSON.stringify(result));
      console.log(JSON.stringify(await client.evaluate('window.__codexQuotaHeaderV1.inspect()')));
      count++;
    } finally{client.close();}
  }
  if(!count)throw Error('No existing quota component found; no application changed');
})().catch(error=>{console.error(error.message);process.exitCode=1;});
