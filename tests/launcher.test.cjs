const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const manager = fs.readFileSync(path.join(__dirname,'../manage.ps1'),'utf8');
const launchers = fs.readFileSync(path.join(__dirname,'../make_launchers.ps1'),'utf8');
test('Default desktop launcher never asks to restart Codex', () => {
  assert.match(launchers, /Name='Codex Quota Header\.lnk';Args='-Action Start'/);
  assert.doesNotMatch(launchers, /Args='[^']*-RestartCodex/);
});
test('No window-close or stop command targets the Codex application', () => {
  assert.doesNotMatch(manager, /CloseMainWindow\s*\(/);
  assert.doesNotMatch(manager, /Stop-Process/);
  assert.match(manager, /Automatic Codex restart is disabled/);
});
test('Interactive Codex launch is visible and launcher errors are logged', () => {
  assert.match(manager, /Start-Process -FilePath \$codexExe[^\r\n]*-WindowStyle Normal/);
  assert.match(manager, /trap \{[\s\S]*AppendAllText\(\$launcherLog/);
});
test('Start does not silently opt in to startup or target another workspace', () => {
  const start = manager.slice(manager.indexOf('$codexExe = Get-CodexPath'));
  assert.doesNotMatch(start, /& \$PSCommandPath -Action InstallStartup/);
  assert.doesNotMatch(manager, /originalFloatingFile|learningFolder|Documents\\ChatGPT/);
  assert.match(manager, /function Assert-OwnedShortcut/);
});
test('Version probes and Python feed are hidden, including child CLI', () => {
  assert.match(manager, /Start-Process -FilePath \$spec.Exe[^\r\n]*-WindowStyle Hidden/);
  const bridge = fs.readFileSync(path.join(__dirname,'../cdp_bridge.cjs'),'utf8');
  assert.match(bridge, /windowsHide:true/);
  const reader = fs.readFileSync(path.join(__dirname,'../account_reader.py'),'utf8');
  assert.match(reader, /CREATE_NO_WINDOW/);
  const feed = fs.readFileSync(path.join(__dirname,'../quota_feed.py'),'utf8');
  assert.doesNotMatch(feed, /from codex_quota_widget/);
});
