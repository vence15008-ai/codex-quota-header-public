/* Own UI only: no conversation text, cookies, tokens, or native app state. */
function installQuotaHeader(state) {
  const KEY = '__codexQuotaHeaderV1';
  const ID = 'codex-quota-header-v1';
  const VERSION = 'window-header-2.3';
  if (window[KEY] && window[KEY].version !== VERSION) window[KEY].remove();
  if (!window[KEY]) {
    const api = { state: {}, requestRefresh: false, version: VERSION };
    let currentHost = null, originalPosition = null, frame = null, disposed = false;
    let observed = [];
    let manualPending=false, manualDispatched=false, feedbackUntil=0;
    let feedbackTimer=null, manualTimeout=null, manualError=null;
    const root = document.createElement('div');
    root.id = ID;
    root.dataset.quotaPlacement = 'window-header';
    const shadow = root.attachShadow({mode: 'open'});
    shadow.innerHTML = `<style>
      :host {position:absolute; top:0; display:flex; box-sizing:border-box; min-width:0;
        align-items:center; justify-content:center; padding:0 6px; pointer-events:auto;
        -webkit-app-region:no-drag; overflow:hidden; color:inherit;}
      .row {display:flex; align-items:center; gap:8px; width:max-content; height:100%;
        flex-shrink:0; white-space:nowrap; color:inherit;
        font:500 13px/1.25 "Microsoft YaHei UI","Segoe UI",sans-serif;}
      .row::-webkit-scrollbar {display:none}
      .group {display:flex; align-items:center; gap:5px; flex-shrink:0}
      [data-text] {font-variant-numeric:tabular-nums; font-weight:600}
      .muted {opacity:.66; font-weight:400; font-size:12px}
      .sep {opacity:.35; margin:0 2px}
      .progress {display:inline-block; width:46px; height:6px; border-radius:8px;
        background:color-mix(in srgb,currentColor 17%,transparent); overflow:hidden}
      .fill {display:block; height:100%; border-radius:8px; background:#60b9f4;
        transition:width .2s ease;}
      button {border:0; background:transparent; color:inherit; padding:3px;
        cursor:pointer; font:16px/1 "Segoe UI",sans-serif; -webkit-app-region:no-drag}
      button:hover {background:color-mix(in srgb,currentColor 10%,transparent); border-radius:4px}
      button:disabled {cursor:progress}
      .refresh-icon {display:inline-block;transform-origin:center}
      :host([data-loading]) .refresh-icon {animation:spin .75s linear infinite;color:var(--color-text-link,#328fd1)}
      .spinner {display:inline-block; width:10px; height:10px; border:2px solid #8ba6bd; border-right-color:transparent;
        border-radius:50%; animation:spin .8s linear infinite; flex-shrink:0;}
      .status {display:flex;align-items:center;justify-content:center;width:14px; flex-shrink:0; text-align:center; font-size:12px}
      .error {color:#e59b52}
      :host([data-density="compact"]) [data-reset],
      :host([data-density="compact"]) .age,
      :host([data-density="mini"]) [data-reset],
      :host([data-density="mini"]) .age,
      :host([data-density="mini"]) [data-group="reserve"],
      :host([data-density="mini"]) .progress,
      :host([data-density="tiny"]) [data-reset],
      :host([data-density="tiny"]) .age,
      :host([data-density="tiny"]) [data-group="reserve"],
      :host([data-density="tiny"]) [data-group="short"],
      :host([data-density="tiny"]) .progress {display:none}
      [hidden] {display:none!important}
      @keyframes spin {to {transform:rotate(360deg)}}
      @media (prefers-reduced-motion:reduce) {.spinner,.refresh-icon {animation:none!important} .fill {transition:none}}
    </style><div class="row" role="group" aria-label="Codex 剩余额度">
      <span class="group" data-group="week"><span data-text="week">周额度 --%</span>
        <span class="progress" role="progressbar" aria-label="周额度剩余" aria-valuemin="0" aria-valuemax="100"><span class="fill"></span></span>
        <span class="muted" data-reset="week">重置 --</span></span>
      <span class="group" data-group="short" hidden><span class="sep">·</span><span data-text="short"></span>
        <span class="progress" role="progressbar" aria-label="5H额度剩余" aria-valuemin="0" aria-valuemax="100"><span class="fill"></span></span>
        <span class="muted" data-reset="short"></span></span>
      <span class="group" data-group="reserve"><span class="sep">·</span><span data-text="reserve">Reserve --%</span></span>
      <span class="group age"><span class="sep">·</span><span class="muted" data-age>尚未更新</span></span>
      <span class="status"><span class="spinner" hidden></span><span class="error" hidden>!</span></span>
      <button type="button" title="刷新额度" aria-label="刷新额度"><span class="refresh-icon" aria-hidden="true">↻</span></button>
    </div>`;
    shadow.querySelector('button').addEventListener('click', () => {
      if(api.state.loading || manualPending || performance.now()<feedbackUntil)return;
      api.requestRefresh=true; manualPending=true; manualDispatched=false; manualError=null;
      feedbackUntil=performance.now()+650;
      // Give immediate feedback instead of waiting for the bridge's 2s poll.
      clearTimeout(feedbackTimer); feedbackTimer=setTimeout(render,660);
      clearTimeout(manualTimeout);
      manualTimeout=setTimeout(()=>{
        manualPending=false;api.requestRefresh=false;
        manualError='未收到刷新结果，请检查额度后台组件';render();
      },90000);
      render();
    });

    function host() {
      // Window chrome, not data-app-shell-titlebar/main-titlebar: those belong
      // to the conversation pane. CSS module prefixes verified in live Codex.
      const candidates = document.querySelectorAll('[class*="ApplicationMenuTopBar"], header[class*="_TitleBar_"], [data-codex-window-header]');
      return [...candidates].filter(el => {
        const rect = el.getBoundingClientRect();
        const style = getComputedStyle(el);
        return rect.height >= 28 && rect.height <= 64 && rect.width >= innerWidth * .8 &&
          rect.top >= 0 && rect.top <= 8 && style.visibility === 'visible' &&
          !el.closest('[inert], [aria-hidden="true"], [data-app-shell-main-content-layout]');
      }).sort((a,b) => a.getBoundingClientRect().top-b.getBoundingClientRect().top)[0];
    }
    function releaseHost() {
      if (currentHost && originalPosition !== null && currentHost.style.position === 'relative') {
        if (originalPosition) currentHost.style.position = originalPosition;
        else currentHost.style.removeProperty('position');
      }
      currentHost = null; originalPosition = null;
    }
    function visible(el) {
      const r=el.getBoundingClientRect(), s=getComputedStyle(el);
      return r.width>0 && r.height>0 && s.visibility==='visible' && s.display!=='none';
    }
    function controls(header) {
      return [...header.querySelectorAll('button,a,input,[role="button"],[role="menuitem"],select')]
        .filter(el=>!root.contains(el)&&visible(el));
    }
    function freeSlot(header, occupied) {
      const r=header.getBoundingClientRect(), style=getComputedStyle(header);
      const start=r.left+parseFloat(style.paddingLeft||0)+6;
      // The native caption buttons sit in the reserved right padding.
      const captionPadding=Math.max(parseFloat(style.paddingRight)||0,
        header.matches('header[class*="_TitleBar_"]')?137:0);
      const end=r.right-captionPadding-6;
      const intervals=occupied.map(el=>el.getBoundingClientRect())
        .filter(b=>b.top<r.bottom&&b.bottom>r.top&&b.right>start&&b.left<end)
        .map(b=>[Math.max(start,b.left-8),Math.min(end,b.right+8)])
        .sort((a,b)=>a[0]-b[0]);
      let cursor=start; const gaps=[];
      for(const [left,right] of intervals) {if(left>cursor)gaps.push([cursor,left]);cursor=Math.max(cursor,right);}
      if(cursor<end)gaps.push([cursor,end]);
      return gaps.filter(([a,b])=>b-a>=100).sort((a,b)=>(b[1]-b[0])-(a[1]-a[0]))[0] || null;
    }
    function schedule() {
      if(disposed)return;
      if(frame===null)frame=requestAnimationFrame(()=>{frame=null;render();});
    }
    const resizeObserver = new ResizeObserver(schedule);
    function layout(header) {
      if (!header) {root.style.display='none';return;}
      if (currentHost!==header || root.parentNode!==header) {
        releaseHost(); currentHost=header;
        if(getComputedStyle(header).position==='static') {originalPosition=header.style.position;header.style.position='relative';}
        header.appendChild(root);
      }
      const occupied = controls(header);
      // Preserve non-interactive native title text, too; ignore empty flex spacers.
      for(const child of header.children) {
        if(child!==root && visible(child) && child.textContent.trim() &&
          child.getBoundingClientRect().width<header.clientWidth*.8) occupied.push(child);
      }
      const targets=[header,...occupied];
      if(targets.length!==observed.length || targets.some((el,i)=>el!==observed[i])) {
        resizeObserver.disconnect(); targets.forEach(el=>resizeObserver.observe(el)); observed=targets;
      }
      const gap=freeSlot(header,occupied);
      if(!gap) {root.style.display='none';return;}
      root.style.display='flex';
      const row=shadow.querySelector('.row'), available=gap[1]-gap[0];
      let width=0;
      for(const density of ['full','compact','mini','tiny']) {
        root.dataset.density=density;
        width=Math.ceil(row.getBoundingClientRect().width)+12;
        if(width<=available)break;
      }
      if(width>available){root.style.display='none';return;}
      const h=header.getBoundingClientRect();
      // Center in the window if possible, then clamp inside the actual free slot.
      const left=Math.max(gap[0],Math.min(innerWidth/2-width/2,gap[1]-width));
      const styles={left:(left-h.left-header.clientLeft)+'px',width:width+'px',height:header.clientHeight+'px'};
      for(const [name,value] of Object.entries(styles))if(root.style[name]!==value)root.style[name]=value;
      api.layout={x:left,y:h.top,width,height:header.clientHeight,density:root.dataset.density,gap};
    }
    function setText(selector, value) {
      const el = shadow.querySelector(selector);
      if (el.textContent !== value) el.textContent = value;
    }
    function reset(epoch) {
      if (!epoch) return '重置未知';
      const d = new Date(epoch * 1000), pad = n => String(n).padStart(2, '0');
      return `重置 ${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    }
    function render() {
      if(disposed)return {mounted:false};
      const header = host();
      const s = api.state;
      for (const [key, label] of [['week','周额度'],['short','5H额度'],['reserve','Reserve']]) {
        const group = shadow.querySelector(`[data-group="${key}"]`);
        const quota = s.view?.[key];
        group.hidden = key === 'short' && !quota;
        if (!quota) continue;
        setText(`[data-text="${key}"]`, `${label} ${Math.round(quota.remaining)}%`);
        group.title = `${label}剩余 ${quota.remaining.toFixed(1)}%`;
        const progress = group.querySelector('.progress');
        if (progress) {
          progress.setAttribute('aria-valuenow', String(quota.remaining));
          const fill = progress.firstElementChild;
          fill.style.width = quota.remaining + '%';
          fill.style.background = quota.remaining < 20 ? '#ed7777' : quota.remaining < 50 ? '#e0aa5b' : '#60b9f4';
          setText(`[data-reset="${key}"]`, reset(quota.resetsAt));
        }
      }
      const minutes = s.updatedAt == null ? null : Math.max(0, Math.floor((Date.now()-s.updatedAt)/60000));
      setText('[data-age]', minutes == null ? '尚未更新' : minutes === 0 ? '刚刚更新' : `${minutes}分钟前更新`);
      const busy=Boolean(s.loading || manualPending || performance.now()<feedbackUntil);
      root.toggleAttribute('data-loading',busy);
      root.setAttribute('aria-busy',String(busy));
      shadow.querySelector('.spinner').hidden = !s.loading;
      const refreshButton=shadow.querySelector('button');
      refreshButton.disabled=busy;
      refreshButton.title=busy?'正在刷新额度…':'刷新额度';
      const error = shadow.querySelector('.error');
      const errorMessage=manualError || s.error;
      error.hidden = !errorMessage;
      error.title = errorMessage || '';
      const details=['周额度','5H额度','Reserve'].map((label,i)=>{
        const quota=s.view?.[['week','short','reserve'][i]];
        return quota?`${label} ${Math.round(quota.remaining)}% · ${reset(quota.resetsAt)}`:null;
      }).filter(Boolean).join('\n');
      root.title = (errorMessage ? `刷新失败，保留上次数据：${errorMessage}\n` : '')+details;
      layout(header);
      return {mounted: Boolean(header && root.isConnected && root.parentNode === header && root.getBoundingClientRect().height>0), headerFound: Boolean(header), height: root.getBoundingClientRect().height,placement:'window-header',density:root.dataset.density};
    }
    api.update = s => {
      // A post-dispatch terminal update acknowledges the manual refresh. It
      // still works if the reader finished before the bridge saw loading=true.
      if(manualPending && manualDispatched && !s.loading) {
        manualPending=false;manualError=null;clearTimeout(manualTimeout);
      }
      // A reader/helper restart must not blank the last visible quota or age.
      api.state = !s.view && api.state.view ? {...s,view:api.state.view,updatedAt:s.updatedAt??api.state.updatedAt} : s;
      return render();
    };
    api.poll = () => {
      const result = render();
      result.refreshRequested = api.requestRefresh;
      if(api.requestRefresh)manualDispatched=true;
      api.requestRefresh = false;
      return result;
    };
    // Only recover removal/navigation; never rebuild the strip on each fetch.
    let pending = false;
    const observer = new MutationObserver(() => {
      if (root.isConnected || pending) return;
      pending = true;
      setTimeout(() => {pending = false; schedule();}, 100);
    });
    observer.observe(document.documentElement, {childList:true, subtree:true});
    const timer = setInterval(render, 5000);
    api.inspect = () => ({...api.layout,placement:'window-header',mounted:root.isConnected&&root.getBoundingClientRect().height>0});
    api.remove = () => {disposed=true;clearTimeout(feedbackTimer);clearTimeout(manualTimeout);observer.disconnect(); resizeObserver.disconnect(); clearInterval(timer);if(frame!==null)cancelAnimationFrame(frame); root.remove(); releaseHost(); delete window[KEY];};
    window[KEY] = api;
  }
  return window[KEY].update(state);
}
