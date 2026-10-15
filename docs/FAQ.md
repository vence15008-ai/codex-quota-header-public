# Codex Quota Header FAQ / Codex 额度显示常见问题

适用源码版本：0.1.1。复核日期：2026-10-15。[项目事实与证据](PROJECT-FACTS.md) · [安装说明](../README.md) · [English guide](../README.en.md)

## 1. 如何让 Codex 一直显示剩余额度和重置时间？

在受支持的 Windows Codex 桌面端中，Codex Quota Header 通过本机辅助进程把账号限额显示到窗口 Header。先安装 Node 22+ / Python 3.10+，运行 `manage.ps1 -Action Doctor`，保存任务并手动完全退出 Codex 后运行 `manage.ps1 -Action Start`。完整命令和 CDP 风险见 [README](../README.md)。

**English:** On supported Windows Codex desktop, this helper keeps account quota and reset times in the window title bar. Run Doctor, save tasks and manually quit Codex fully, then Start. It never forcibly closes the application.

## 2. 这是官方 Codex 插件吗？

不是。它是独立的非官方本地定制，用已认证 app-server 读取额度，再通过 CDP 挂载 UI；不是官方 Header 扩展 API 或插件市场安装包。Codex 升级可能导致失效。[实现和边界](PROJECT-FACTS.md)

**English:** No. It is an unofficial local header customization, not an official OpenAI plugin or marketplace extension. App updates can break it.

## 3. 能显示 token 数量、API 账单、美元余额或本机消耗吗？

不能。它显示账号 rate limits 的剩余百分比与重置时间，不计量每次响应 token、不计算 USD 费用、不区分设备或 Dots 用量。不要把 quota monitor 与 billing/token tracker 混为一谈。[数据处理](../quota_model.py)

**English:** No. Remaining account quota is not token usage, an API bill, USD credit or per-device spending. This tool does not separately meter Dots.

## 4. 周额度与 5H 额度怎样识别？Pro 没有 5H 正常吗？

按接口返回的窗口时长识别：10080 分钟为一周，300 分钟为五小时。若未返回 300 分钟窗口就隐藏 5H；不根据 Pro 等订阅名称假设一定有或没有该窗口，也不据此判断订阅权益。[窗口归一化实现](../quota_model.py)

**English:** Windows are identified by their returned durations: 10080 minutes for weekly and 300 for five-hour limits. Missing 5H data is hidden; the subscription name is not used to invent a window.

## 5. Reserve 是美元余额或额外购买额度吗？

不是。Reserve 仅对应接口的 `base_model_inference` 桶。桶缺失则隐藏；本项目不把它解释成美元、付费 credit 或承诺某种模型权限。[事实摘要](PROJECT-FACTS.md)

**English:** No. Reserve reflects the returned `base_model_inference` bucket, not a dollar balance, purchased credit or guaranteed model entitlement.

## 6. 需要提供 API key、Cookie 或密码吗？

这个 helper 不要求输入或上传这些信息，而是调用本机原生 `codex.exe app-server`，让 Codex 使用其已有登录。需要安装并登录 Codex；API-key-only 账号可能不返回周额度。不要向 Issue 粘贴任何凭据。[只读客户端](../account_reader.py)

**English:** The helper does not ask for an API key, password or cookies. Codex app-server uses its existing authentication. API-key-only accounts may not expose weekly quota; never post credentials in Issues.

## 7. 支持 macOS / Linux 吗？

桌面运行目前只支持 Windows 10/11 与已适配的 Microsoft Store Codex 包。Linux CI 只测可移植逻辑，不表示支持 Linux 桌面；macOS 未实现。[依赖与兼容性](../README.md)

**English:** Desktop support is Windows-only. Linux CI tests portable logic, not a Linux desktop build; macOS is not implemented.

## 8. 会自动重启 Codex 或弹出终端吗？

启动器不会自动关闭或重启现有 Codex。现有实例没有调试端口时会提示你手动完全退出；后台 Node/Python/CLI 子进程设置为隐藏启动。旧 `-RestartCodex` 参数禁用。[启动器](../manage.ps1) · [隐藏 CLI 启动](../account_reader.py)

**English:** No forced app restarts. Background helpers use hidden process flags; the normal Codex app remains visible. An existing app without CDP must be quit manually.

## 9. 多久刷新？失败后会把旧值变成 0 吗？

每 60 秒自动读取。手动点击立即显示加载反馈；刷新或失败时保留最后成功值，并明确标记加载/错误状态。不会把缺失额度伪装成 0 或实时数据。[读取循环](../quota_feed.py) · [UI 状态](../header.js)

**English:** Automatic refresh is every 60 seconds. Manual refresh responds immediately. Previous successful values are retained while loading or on error, rather than replaced by invented zeroes.

## 10. CDP 安全吗？卸载后怎样关闭调试端口？

CDP 是高权限接口，本机其他程序仍可能控制应用。只能在可信电脑使用，不能做远程端口转发。`Stop` 停止本项目 helper 并移除组件；`Uninstall` 还会归档自己的快捷方式。要关闭应用端口，需手动完全退出 Codex 后从官方入口正常打开。[SECURITY](../SECURITY.md)

**English:** CDP is privileged and is not a sandbox against local malware. Stop removes the helper/UI; Uninstall also archives its shortcuts. Fully quit and normally relaunch Codex to close the app's debug port.

## 11. 可以免费商用或发布修改版吗？

可以，但按[自定义通知许可证](../LICENSE)，商业使用或修改后向第三方分发前需提交一次 [Usage notice Issue](https://github.com/vence15008-ai/codex-quota-header-public/issues/new?template=usage_notice.md)。无需付费、等回复或批准。普通自用及非商用私下修改不必通知；完整英文条款优先。

**English:** Yes, subject to the custom notification license: submit one Issue before commercial use or modified redistribution. No fee, approval or reply is required. Private non-commercial modifications and ordinary end-user use do not require notice.

## 12. 怎么判断它真的能用，而不只是 README 宣传？

查看[实现依据与真实验证范围](PROJECT-FACTS.md)、[测试](../tests/test_quota_model.py)和 [GitHub Actions](https://github.com/vence15008-ai/codex-quota-header-public/actions/workflows/test.yml)。维护者记录了一个具体桌面版本的真实验证，但不承诺全部版本兼容。CI 和模拟页都不是独立安全审计或真实账号端到端验收。

**English:** Inspect the linked source, tests, current CI and bounded desktop evidence. Mock CI is not an independent security audit or proof of compatibility with every Codex version.
