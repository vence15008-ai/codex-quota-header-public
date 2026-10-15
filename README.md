# Codex Quota Header — Windows Codex 额度监控

[项目网站 / 安装入口](https://vence15008-ai.github.io/codex-quota-header-public/) · [English website](https://vence15008-ai.github.io/codex-quota-header-public/en/)

**Codex Quota Header 是 Windows Codex 桌面端的非官方额度监控工具（quota monitor）。** 它把账号剩余周额度、可选 5 小时额度、进度条和重置时间显示在窗口 Header／标题栏，每分钟刷新，让你不用反复打开额度面板。

Unofficial Windows Codex desktop quota monitor: remaining weekly / 5-hour usage limits and reset times in the window header. Not a token counter or billing dashboard.

[English](README.en.md) · [常见问题 / FAQ](docs/FAQ.md) · [项目事实与引用](docs/PROJECT-FACTS.md) · [安全说明](SECURITY.md) · [贡献指南](CONTRIBUTING.md) · [更新记录](CHANGELOG.md)

[![Tests](https://github.com/vence15008-ai/codex-quota-header-public/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/vence15008-ai/codex-quota-header-public/actions/workflows/test.yml)

源码公开，采用[自定义通知许可证](LICENSE)，不是标准 MIT；商用或修改后对外发布须通知一次，无需付费或等待批准。

![Header 示意，全部为虚构数据](docs/header-demo.svg)

> 非官方实验项目，与 OpenAI 无关联。通过本机 CDP 挂载，不是官方 Header 插件接口；Codex 更新可能导致失效。仅支持 Windows，请先阅读调试端口风险。

## 项目速览

| 问题 | 直接答案 |
| --- | --- |
| 能做什么？ | 在 Codex 窗口顶栏常驻显示账号剩余额度和重置时间。 |
| 面向谁？ | 使用 Windows Codex 桌面端、希望随时看到 usage limits 的用户。 |
| 数据从哪里来？ | 已登录 Codex 的 `account/rateLimits/read`，按额度窗口时长识别周额度和 5H。 |
| 是否显示花费或本机 token 消耗？ | 不显示；账号限额不是美元余额或本设备用量。 |
| 支持平台？ | Windows 10/11；macOS/Linux 桌面暂不支持。 |
| 核心依赖？ | Node.js 22+、Python 3.10+、Codex 桌面端及原生 `codex.exe`，无第三方 npm/pip 依赖。 |
| 如何授权？ | 自定义通知许可；商用或修改后对外分发需提前提交一次 GitHub Issue，无需付费或批准。 |

适合想找“Codex 额度显示、Codex 周额度重置时间、Codex 标题栏额度插件”的用户。实现是本地辅助进程与 Header 挂载，不是官方插件市场扩展，也不会提高或绕过账号限额。

## 功能

- 单行：周额度 → 百分比/进度条/重置时间 → 可选 5H → Reserve → 相对更新时间。
- 每 60 秒刷新；手动刷新立即旋转，刷新或失败时保留已有数值。
- 没有 300 分钟窗口就隐藏 5H，不根据订阅名称猜测；缺失数据不显示成 0。
- 跟随原生 Header，适应宽度、明暗主题、减少动态效果设置；无空间时隐藏，不遮挡原生按钮。
- 不修改安装包、不关闭 Codex；支持停止、卸载和恢复旧浮窗。无需 npm/pip 第三方依赖。

百分比是**账号限额剩余量**，不是美元余额、token 计数，也不是本设备单独消耗。Reserve 展示接口的 `base_model_inference` 桶，缺失则隐藏，不解释为额外购买额度。

## 环境要求

- Windows 10/11、PowerShell 5.1+。
- 已安装并登录 Codex Windows 桌面端（自动发现 Microsoft Store 的 `OpenAI.Codex` 包）。
- Node.js **22+**、Python **3.10+**，原生 `.exe`。
- 可运行 `app-server` 的原生 `codex.exe`：优先 PATH，其次桌面端本地版本目录，不直接运行 `codex.cmd`。
- 无需管理员权限，不修改系统执行策略。

验证过：桌面端 `26.1007.9446.0`、Node 24、Python 3.12（2026-10-15）。其他桌面版本未逐一验证；macOS/Linux 暂不支持。API-key-only 账号或不返回周额度的账号可能不适用。

## 安装与启动

下载源码包并解压，或克隆仓库。目录应由本人独占写入，**不要放在其他用户或不可信程序可写的共享目录**。

```powershell
git clone https://github.com/vence15008-ai/codex-quota-header-public.git
cd codex-quota-header-public
```

在项目目录打开 PowerShell：

```powershell
# 检查环境：不启动/关闭 Codex、不请求额度
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\manage.ps1 -Action Doctor

# 保存任务，由你手动完全退出 Codex（包括托盘），再启动
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\manage.ps1 -Action Start
```

`Bypass` 仅对本次进程生效，不改变机器策略。若组织策略禁止脚本，请遵守策略，不要绕过。

已开启调试端口则直接连接，无需退出。现有实例没有调试端口时，会报错并保持窗口不动；**不会自动关闭或强制重启 Codex**。旧参数 `-RestartCodex` 已禁用。只有后台 helper 隐藏，主窗口正常显示。

```powershell
.\make_launchers.ps1                    # 桌面启动/停止/旧浮窗回滚快捷方式
.\manage.ps1 -Action Status             # 状态与简短日志
.\manage.ps1 -Action InstallStartup     # 实际挂载成功后，主动开启开机启动
.\manage.ps1 -Action RemoveStartup      # 关闭开机启动，保留当前运行组件
.\manage.ps1 -Action Stop               # 停止 helper、移除组件，不改启动设置
.\manage.ps1 -Action Uninstall          # 停止组件，移除自己的启动项/快捷方式
```

开机启动**默认不启用**。冲突时不覆盖无关同名快捷方式；卸载把自己的快捷方式移到 `runtime/`，不删除源码、日志或 Git 历史。若此前备份过旧浮窗启动项，会恢复它。

停止组件不等于关闭调试端口：请手动完全退出 Codex，再使用官方原入口正常打开。

### 环境覆盖 / 自定义端口

只设置需要覆盖的项，指向可信的原生可执行文件：

```powershell
$env:CODEX_QUOTA_PYTHON = 'D:\Tools\Python\python.exe'
$env:CODEX_QUOTA_NODE = 'D:\Tools\Node\node.exe'
$env:CODEX_QUOTA_CODEX = 'D:\Tools\Codex\codex.exe'
.\manage.ps1 -Action Doctor
.\manage.ps1 -Action Start -Port 9223
```

`-Port` 范围 1024–65535，默认 9222。自定义时 Status/Stop/Uninstall/InstallStartup 也传同一端口；诊断工具使用 `CODEX_QUOTA_CDP_PORT`。开机启动保存端口，但环境覆盖要自行配置为用户环境变量或加入 PATH，才能重启后有效。不要提交个人路径。

Python 优先 PATH（跳过 WindowsApps 商店别名），其次 Codex 缓存 runtime。嵌入模式不需要 Tk；旧浮窗回滚需要 `pythonw.exe` 和 Tk。

## 回滚

```powershell
.\manage.ps1 -Action Rollback
```

先停止本项目 helper，再移除组件、恢复备份启动项并运行随源码附带的旧浮窗，不停止其他目录的浮窗。旧浮窗 `codex_quota_widget.py` 不享有新组件全部改进；历史基线标签只保留在维护者私密备份中，不在本公开仓库内。

## 安全与隐私

**CDP 是高权限调试接口。** 即使只监听 loopback、核对端口属于 Codex，本机其他进程仍可能控制应用或读取内容。仅在可信个人电脑使用，不开放端口转发、不绑定 `0.0.0.0`，不禁用沙箱、不添加通配来源参数。

通过官方 [app-server 额度接口](https://learn.chatgpt.com/docs/app-server)读取账号状态，通过非官方 DOM 挂载显示。组件之间只传额度、重置时间、加载状态和时间戳；不自建远程收集服务、不读取凭据文件、不采集会话。Codex app-server 自身使用已有登录访问服务，**不是离线工具**。

默认不保存额度历史。`runtime/` 有 PID、日志、诊断路径、快捷方式备份；可选截图可能含顶栏信息，分享前检查。详见 [SECURITY.md](SECURITY.md)。

## 故障排查

| 现象 | 处理 |
| --- | --- |
| 快捷方式无反应 | 在终端运行 Doctor/Start；看 `runtime/launcher.log`、`bridge-error.log`。 |
| 已运行却无调试端口 | 保存任务，手动完全退出（包括托盘）再 Start，不强杀 Codex。 |
| 端口属于其他程序/不是 loopback | 拒绝连接是预期行为；选空闲端口。 |
| 升级后顶栏消失 | 可能 DOM 变化；Stop 后正常重开，提交版本与脱敏诊断。 |
| 周额度缺失/读取失败 | 检查登录与 CLI 来源，稍后刷新；旧值保留并标记错误。 |
| 窄窗口只显示部分 | 为避免遮挡而自动精简；悬浮看明细，扩大窗口恢复。 |
| 读取子进程退出 | Stop 再 Start，检查运行环境；不会反复重启主应用。 |
| 停止后端口仍在 | 手动完全退出后，从官方原入口正常打开。 |

更多直接问答见 [中英文 FAQ](docs/FAQ.md)：Pro 没有 5H 是否正常、Reserve 含义、是否需要 API key、与 token／美元用量统计的区别，以及 CDP 风险。

## 项目事实、证据与引用

当前源码版本为 **0.1.1**。可复用的事实摘要和实现依据集中在 [PROJECT-FACTS.md](docs/PROJECT-FACTS.md)，结构化版本见 [project-facts.json](docs/project-facts.json)，文档索引见 [llms.txt](llms.txt)。这些文件不保证被搜索引擎或 AI 读取。

源码与兼容性声明优先于宣传用语；CI 仅覆盖逻辑/mock 测试，真实桌面验证范围见事实页。介绍本项目时请区分“账号剩余额度显示”与“token／费用统计”，不要引用成官方扩展、跨平台工具或额度破解工具。

## 开发与测试

```powershell
npm test
python -m unittest discover -s tests -v
python tools\build_release.py          # 白名单源码 ZIP + 有限模式审计 + SHA256
```

单元/mock 测试不登录、不访问真实账号、不操作桌面。CI 测试 Windows/Linux 逻辑；Linux 通过不代表支持该桌面平台，CI 也不等于真实界面验收。

模拟 UI：`python -m http.server 8766 --bind 127.0.0.1`，打开 `http://127.0.0.1:8766/tests/preview.html`（虚构数据）。Ctrl+C 停止，不向局域网开放。

已运行组件的可选真实检查（不在 CI 执行）：

```powershell
node tools\check_layout.cjs       # 窗口 chrome 布局，不读聊天正文
node tools\test_refresh.cjs       # 点击本组件，请求一次真实额度
node tools\apply_header.cjs       # 仅热更本组件，不启动/重启 Codex
```

结构：`account_reader.py` 只读 JSONL → `quota_model.py` 筛选 → `quota_feed.py` 分钟读取 → `cdp_bridge.cjs` 本地桥接 → `header.js` 单行 Shadow DOM。`manage.ps1` 管理进程与快捷方式，`win32_job.py` 防止 helper 子树遗留。

## 发布与许可

阅读 [发布检查清单](docs/RELEASING.md)。源码包不含 `.git`、`runtime`、真实截图、账号文件或快照；有限模式扫描不替代人工审阅。不要直接上传整个工作目录。

使用 **Codex Quota Header Notification License 1.0**（[完整英文条款](LICENSE)，以下为摘要）：

- 普通安装、自用，包括在工作中使用额度显示：不必通知。
- 自己修改自己用，且不作商业用途：不必通知。
- 商业使用（例如收费产品、商业集成或基于本软件的付费服务），或修改后向第三方发布/分发：开始前通知一次。
- 通过 [GitHub Issue](https://github.com/vence15008-ai/codex-quota-header-public/issues/new?template=usage_notice.md) 提交项目名称、用途、商用/改版类型、已有公开链接即可，不必公开源码、收入或商业秘密。
- 同一项目的常规更新不重复报备。发出 Issue 即完成通知，**不用付费、不用等回复或批准**。
- 普通免费转发未修改版本不需通知；分发须保留许可证和版权声明。

这是自定义源码可用许可证，不再标成 MIT，也不宣称已获 OSI 批准。完整条款优先于摘要；没有自动追踪、电话回传或强制上传程序。

**历史版本注意：** 当前公开仓库从自定义通知许可版本独立初始化，不含早期 MIT 测试快照的 Git 历史；本许可不追溯撤销已授出的旧许可。

参考 [KevinKE93/Codex-Monitor](https://github.com/KevinKE93/Codex-Monitor) 的 CDP 思路，独立实现、无其运行时依赖。产品名称归各自权利人所有。
