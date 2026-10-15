const fs=require('node:fs');
const path=require('node:path');
const {CDP,targets}=require('../cdp_bridge.cjs');
(async()=>{
  const found=await targets();
  let checked=0;
  for(const target of found){
    const client=new CDP(target.webSocketDebuggerUrl);
    try{
      const check=await client.evaluate(`(()=>{
        const root=document.getElementById('codex-quota-header-v1');
        if(!root||root.getBoundingClientRect().height===0)return null;
        const r=root.getBoundingClientRect(), header=root.parentElement,h=header.getBoundingClientRect();
        const overlap=[...header.querySelectorAll('button,a,[role="button"],[role="menuitem"]')].filter(el=>{
          const b=el.getBoundingClientRect();return b.width&&b.height&&getComputedStyle(el).visibility==='visible'&&
            r.left<b.right&&r.right>b.left&&r.top<b.bottom&&r.bottom>b.top;
        }).length;
        return {viewportWidth:innerWidth,y:r.y,height:r.height,headerHeight:header.clientHeight,overlappingControls:overlap,
          conversationMounted:!!root.closest('[data-app-shell-titlebar],[data-app-shell-main-titlebar]'),
          captionSafe:r.right<=h.right-parseFloat(getComputedStyle(header).paddingRight||0),
          layout:window.__codexQuotaHeaderV1.inspect(),hasLiveQuota:!!window.__codexQuotaHeaderV1.state.view?.week};
      })()`);
      if(!check)continue;
      checked++;
      console.log(JSON.stringify(check));
      if(process.argv.includes('--capture')&&check.viewportWidth>1000){
        // Preserve transparent native chrome; never change app theme for capture.
        const image=await client.call('Page.captureScreenshot',{format:'png',clip:{x:0,y:0,width:check.viewportWidth,height:105,scale:1},captureBeyondViewport:false});
        const output=path.join(__dirname,'../runtime/window-header-live.png');
        fs.writeFileSync(output,Buffer.from(image.data,'base64'));
        console.log('Screenshot: '+output);
      }
      if(check.overlappingControls||check.conversationMounted||check.y>8)process.exitCode=1;
    }finally{client.close();}
  }
  if(!checked)throw new Error('No mounted quota header; layout was not verified');
})().catch(error=>{console.error(error.message);process.exitCode=1;});
