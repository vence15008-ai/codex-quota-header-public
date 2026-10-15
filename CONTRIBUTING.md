# Contributing

感谢贡献。优先兼容性、可访问性、错误恢复和安全，不添加账号采集或聊天内容读取。

当前为自定义通知许可证，不是 MIT。贡献前阅读 [LICENSE](LICENSE)；请确认有权按该许可贡献。单纯提交 PR 不要求另外报备；若同时商用或发布自己的修改版，仍须按许可提交 Usage notice。不开设自动追踪，不把通知变成收费或审批。

1. 独立分支，说明场景、复现步骤和 Windows/Codex/Node/Python 版本。
2. 不提交凭据、会话、真实额度截图、日志或绝对个人路径。
3. 不引入强制关闭应用、全局进程清理、远程监听、安装包补丁、自动提权或全局修改执行策略。
4. 运行 `npm test`、`python -m unittest discover -s tests -v`、`python tools/build_release.py`。
5. PowerShell 修改在 Windows PowerShell 5.1 解析/检查。UI 先测虚构数据，再自愿真实验收，写明未测范围。
6. Header 行为变化时更新 `header.js` 版本标识，保留加载时数值与减少动态效果支持。

Live tools are opt-in, never CI or someone else's app. Tests must not log in, send messages, read credentials or change subscriptions. Actions use read-only permissions and pinned commits.

Scope is account quota display, not billing, per-device attribution, browser extensions or general desktop automation. Keep changes small/reversible. Passing mocks do not prove a real desktop mount.
