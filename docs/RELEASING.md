# 发布检查清单

不要把本地验证写成 GitHub CI 已通过。

## 本地

- [ ] 确认分支、变更和许可证符合意图。
- [ ] 当前版为 `0.1.1` 自定义通知许可，不标 MIT 或 OSI-approved；README、LICENSE、package 元数据和 Issue 模板一致。
- [ ] Node/Python 测试通过，Windows PowerShell 5.1 解析通过。
- [ ] Doctor 不关窗、不请求额度；自愿真实 Header/刷新验收，记录桌面版本及未测范围。
- [ ] `python tools/build_release.py` 生成源码 ZIP 和 SHA256。
- [ ] 源码变动后运行 `python tools/build_release.py --update-manifest`，同步已跟踪的 SOURCE-MANIFEST.json；不改写早期已发布包。
- [ ] 版本、平台和许可变化时同步 PROJECT-FACTS、project-facts.json、FAQ、llms.txt 与 package 元数据，不把它们当作 SEO 排名保证。
- [ ] 再人工看一次 ZIP 清单/文本，有限模式扫描不是安全认证。
- [ ] 运行 `python tools/audit_history.py` 扫描可达历史文本，并另看所有分支、标签、作者元数据和文件名。
- [ ] 不上传 runtime、真实截图、账号/聊天、机器路径或其他项目资料。

## GitHub

- [ ] 决定新公开仓库还是公开已有私密仓库。后者会公开可达历史、分支、标签，不能只检查当前文件。
- [ ] 旧 `0.1.0` / `47d7538` 存有 MIT，公开这些旧副本可能允许按旧条款使用；新许可不能追溯收回授权。建议保留私密历史，新公开仓库只从当前已审阅源码初始化。不要擅自改写/强推旧历史。
- [ ] 新仓库若改名或更换所有者，更新 LICENSE、README、package 的通知链接及一致性测试。
- [ ] 发布前确认通知仓库公开且 Issues 对普通 GitHub 用户开放，不限 Collaborators only，Usage notice 模板可选；私密仓库里的链接不等于外部用户现在可通知。
- [ ] 保持通知 Issue 的可提交性并关注 GitHub 通知；不承诺每条消息一定送达手机。
- [ ] 若旧历史含个人信息，保留私密回滚仓库，在新公开仓库从已审阅源码初始化；不擅自清洗/强推私密备份。
- [ ] 仓库公开、新建仓库、推送和 Release 由所有者明确决定。
- [ ] 在待发布分支实际运行 CI，确认 Windows/Linux mock 和 Windows PowerShell 解析通过。
- [ ] 可启用 private vulnerability reporting，勿承诺不存在的私密联络方式。
- [ ] 确认版本后更新 CHANGELOG、打 `v0.1.1`，上传已审阅 ZIP 与校验值，不上传旧 MIT 的 `0.1.0` 包。
- [ ] 声明非官方、Windows-only、CDP 高权限和兼容性边界。

GitHub 自动 Source code 归档使用仓库内容而非本打包器白名单。构建包排除 `.git`，不代表仓库历史没有隐私；公开仓库前必须独立审计历史。
