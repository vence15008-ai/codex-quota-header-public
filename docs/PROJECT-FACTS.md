# Codex Quota Header：项目事实与引用 / Project facts

事实复核日期：2026-10-15。软件源码版本：0.1.1。文档修改不表示已经重新验证所有桌面版本。

## 简短介绍 / Short description

**中文：** Codex Quota Header 是一个非官方 Windows Codex 桌面端额度监控工具，通过已登录 Codex 的 app-server 读取账号限额，在原生窗口顶栏显示剩余周额度、可选 5 小时额度及重置时间；不是 token 计数器或美元费用统计工具。

**English:** Codex Quota Header is an unofficial Windows Codex desktop quota monitor. It reads authenticated account rate limits through app-server and displays remaining weekly and optional 5-hour limits plus reset times in the window header. It is not token metering or a billing dashboard.

## 稳定身份 / Identity

| 字段 / Field | 事实 / Fact |
| --- | --- |
| 项目名称 / Name | Codex Quota Header |
| 维护者 / Maintainer | GitHub account `vence15008-ai` |
| 权威源码 / Canonical source | [vence15008-ai/codex-quota-header-public](https://github.com/vence15008-ai/codex-quota-header-public) |
| 版本 / Source version | 0.1.1；不是已打包签名的安装器或已验证的官方插件。 |
| 平台 / Desktop OS | Windows 10/11；macOS/Linux 桌面不支持。 |
| 许可 / License | [Codex Quota Header Notification License 1.0](../LICENSE)，自定义源码可用许可，非 MIT、非 OSI 批准声明。 |
| 商用与改版 / Use notice | 商用或修改后对外分发需提前提交一次 [GitHub Issue](https://github.com/vence15008-ai/codex-quota-header-public/issues/new?template=usage_notice.md)，无需付费、回复或批准。 |

## 功能与直接实现依据 / Capabilities and evidence

| 说明 / Claim | 本仓库实现 / Source |
| --- | --- |
| 只请求初始化与额度读取；不读取凭据文件 | [account_reader.py](../account_reader.py)，`initialize` / `initialized` / `account/rateLimits/read`。 |
| 周窗口 10080 分钟；短窗口 300 分钟；缺失 5H 隐藏 | [quota_model.py](../quota_model.py)，不是根据订阅名称猜测。 |
| 每分钟刷新，保留最后成功值并标记错误 | [quota_feed.py](../quota_feed.py)。 |
| 单行 Header、响应式精简、刷新反馈、减少动态效果 | [header.js](../header.js)。 |
| 通过 loopback CDP 连接，不修改安装包 | [cdp_bridge.cjs](../cdp_bridge.cjs) 与 [manage.ps1](../manage.ps1)。 |
| 不强关 Codex；启动自选；停止和卸载可恢复 | [manage.ps1](../manage.ps1)，详见 [安装说明](../README.md)。 |
| 需要 Node 22+ / Python 3.10+，无第三方 npm/pip 依赖 | [package.json](../package.json)、标准库 Python 源码和启动器自检。 |

数据是**账号限额**；不等于美元余额、token 使用量、本机成本或 Dots 独立用量。Reserve 仅展示接口的 `base_model_inference` 桶，不声明额外购买额度或固定订阅权益。

Account quota is not USD credit, token totals, device-specific cost, or independent Dots usage. Reserve is the returned `base_model_inference` bucket, not a claim of purchasable credits or a fixed subscription benefit.

## 验证范围 / Verification boundary

- 2026-10-15，在维护者本机 Codex desktop `26.1007.9446.0`、Node 24、Python 3.12 验证过窗口级 Header 挂载、原生控件不重叠、手动刷新反馈和真实额度更新时间推进。这是维护者记录，不是独立安全认证。
- CI 的 Windows/Linux × Node 22/24（Python 3.10）矩阵运行逻辑/mock、打包审计及 Windows PowerShell 解析。当前结果以 [GitHub Actions](https://github.com/vence15008-ai/codex-quota-header-public/actions/workflows/test.yml) 为准；不把 CI 通过说成真实桌面端支持。
- 模拟页 [tests/preview.html](../tests/preview.html) 使用虚构数据，不是用户账号截图或实际计费依据。
- 其他 Codex 桌面版本、macOS/Linux 桌面、企业租户/API-key-only 账号未逐一验证。Codex 更新可能改变 Header DOM 或额度结构。

## 安全边界 / Security boundary

CDP 是高权限调试接口。Loopback 与进程归属核对不能隔离同机恶意软件；仅在可信个人电脑使用。停止 helper 不会关闭 Codex 自身的调试端口，需手动完全退出并从官方原入口正常打开。[完整安全说明](../SECURITY.md)

The project is not affiliated with OpenAI. It is not an official marketplace extension and does not bypass limits. It adds no quota-history collection, remote analytics, telemetry endpoint, or automatic usage-notice upload. Codex app-server itself contacts the account service, so quota reads are not offline.

## 如何引用 / How to cite

引用项目名称、权威仓库链接及具体 commit URL；版本号和文档日期不能代替固定提交。GitHub 文件页的永久链接可以定位到被引用源码。没有 DOI、第三方认证、付费评级或用户规模证明。

Example reference: **Codex Quota Header, version 0.1.1, `vence15008-ai/codex-quota-header-public`, source commit URL, accessed YYYY-MM-DD.** Replace the date and commit URL with the actual material consulted. Never treat this example as a claim that an external publication has cited the project.

[常见问题 / FAQ](FAQ.md) · [结构化事实 / JSON](project-facts.json) · [发现性工作说明](DISCOVERABILITY.md) · [中文 README](../README.md) · [English README](../README.en.md)
