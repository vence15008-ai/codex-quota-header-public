// Read chrome layout only, never conversation text, credentials, or app state.
const {CDP,targets} = require('../cdp_bridge.cjs');
(async()=>{
  const found = await targets();
  for(const target of found) {
    const client = new CDP(target.webSocketDebuggerUrl);
    try {
      const result = await client.evaluate(`(() => {
        const rect = el => {const r=el.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};};
        const description = el => ({tag:el.tagName, cls:typeof el.className==='string'?el.className.slice(0,500):'',
          attrs:[...el.attributes].filter(a=>a.name.startsWith('data-app-shell')).map(a=>[a.name,a.value]),
          box:rect(el), display:getComputedStyle(el).display, position:getComputedStyle(el).position,
          appRegion:getComputedStyle(el).getPropertyValue('-webkit-app-region')});
        const selectors='[data-app-shell-titlebar],[data-app-shell-main-titlebar],[data-app-shell-header-layout],[data-app-shell-header-slot],[data-app-shell-titlebar-slot],[data-app-shell-application-menu-bar],header,[role="banner"],[class*="titlebar"],[class*="Titlebar"]';
        const headers=[...document.querySelectorAll('[class*="ApplicationMenuTopBar"],header[class*="_TitleBar_"]')].filter(el=>{const r=rect(el);return r.h>0&&r.y<40;}).map(el=>({...description(el),visible:getComputedStyle(el).visibility,padding:getComputedStyle(el).padding,
          controls:[...el.querySelectorAll('button,[role="menubar"],[role="button"],[role="menuitem"]')].map(description),
          children:[...el.children].slice(0,12).map(c=>({...description(c),children:[...c.children].slice(0,8).map(description)}))}));
        const own=document.getElementById('codex-quota-header-v1');
        return {viewport:{w:innerWidth,h:innerHeight},headers,widget:own?{box:rect(own),parent:description(own.parentElement)}:null};
      })()`);
      if(result.widget) console.log(JSON.stringify(result,null,2));
    } finally {client.close();}
  }
})().catch(e=>{console.error(e.message);process.exitCode=1;});
