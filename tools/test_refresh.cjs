// Exercise only this component's refresh button, not the Codex application UI.
const assert=require('node:assert/strict');
const {CDP,targets}=require('../cdp_bridge.cjs');
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
  const found=await targets();
  const candidates=[];
  for(const target of found){
    const c=new CDP(target.webSocketDebuggerUrl);
    try{
      const width=await c.evaluate('document.getElementById("codex-quota-header-v1")?.getBoundingClientRect().height>0?innerWidth:0');
      if(width)candidates.push({target,width});
    }finally{c.close();}
  }
  candidates.sort((a,b)=>b.width-a.width);
  assert.ok(candidates.length,'No mounted quota header');
  const client=new CDP(candidates[0].target.webSocketDebuggerUrl);
  const snapshot=`(()=>{const r=document.getElementById('codex-quota-header-v1'),s=r.shadowRoot,b=s.querySelector('button'),icon=s.querySelector('.refresh-icon');return {busy:r.getAttribute('aria-busy')==='true',disabled:b.disabled,animation:getComputedStyle(icon).animationName,transform:getComputedStyle(icon).transform,reducedMotion:matchMedia('(prefers-reduced-motion:reduce)').matches,week:s.querySelector('[data-text="week"]').textContent,updatedAt:window.__codexQuotaHeaderV1.state.updatedAt};})()`;
  try{
    let before=await client.evaluate(snapshot);
    for(let i=0;before.busy&&i<20;i++){await pause(300);before=await client.evaluate(snapshot);}
    assert.equal(before.busy,false,'Already refreshing; retry test later');
    const immediate=await client.evaluate(`(()=>{const root=document.getElementById('codex-quota-header-v1');root.shadowRoot.querySelector('button').click();return ${snapshot};})()`);
    assert.ok(immediate.busy&&immediate.disabled,'Click must give synchronous busy feedback');
    assert.equal(immediate.week,before.week,'Quota must remain visible');
    if(!immediate.reducedMotion)assert.equal(immediate.animation,'spin');
    await pause(180);
    const moving=await client.evaluate(snapshot);
    if(!immediate.reducedMotion)assert.notEqual(moving.transform,immediate.transform,'Icon must actually rotate');
    let completed=moving;
    for(let i=0;completed.busy&&i<30;i++){await pause(400);completed=await client.evaluate(snapshot);}
    assert.equal(completed.busy,false,'Refresh must finish');
    assert.equal(completed.disabled,false,'Button must re-enable');
    assert.ok(completed.updatedAt>before.updatedAt,'Actual quota refresh must reach the reader');
    console.log(JSON.stringify({immediateFeedback:true,rotates:immediate.reducedMotion?'reduced-motion preference respected':true,retainsQuota:true,completed:true,liveTimestampAdvanced:true}));
  }finally{client.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
