# 仓库 GEO / SEO 工作说明

适用对象：[Codex Quota Header](../README.md)，2026-10-15。这里记录的是可维护的发现性与内容质量措施，不是搜索排名、收录、流量或 AI 引用结果的证明。

## 已实现的仓库层措施

- 中英文标题与首段统一项目名称、Windows 平台、quota monitor 用途；明确与 billing/token tracking 的区别。
- README 速览、可执行安装步骤、FAQ、事实页、实现源码和 CI 相互链接，主要信息保持可读文本，不藏在截图里。
- [项目事实 JSON](project-facts.json)与[事实页](PROJECT-FACTS.md)列出版本、复核日期、维护者、许可证、风险和验证边界；不伪造认证、用户数、星标、费用统计或模型推荐。
- package 元数据与建议的 GitHub Topics 使用实际功能相关词，不把不支持的平台、MIT 或额度破解当作引流标签。
- [llms.txt](../llms.txt)仅作为可选文档导航，供主动读取的工具使用；不声称平台必须读取或它能提高排名。
- 保留软件原有功能和通知许可；没有新增遥测、付费推广或自动对外发帖。

## 搜索意图

| 用户问题 | 入口 | 回答边界 |
| --- | --- | --- |
| Codex 额度怎么常驻显示？ | README、FAQ 1 | 非官方 Windows 标题栏工具，不是官方插件。 |
| Codex 周额度 / 5H 什么时候重置？ | README、FAQ 4 | 显示账号接口返回值，不承诺统一权益或固定日期。 |
| Codex quota monitor / usage limits in title bar | English README、facts | Windows-only account quota, not billing. |
| 能统计本机 token / USD / Dots 花费吗？ | FAQ 3、facts | 当前不能，不以相关关键词冒充已有功能。 |
| 商用或改版要收费吗？ | LICENSE、FAQ 11 | 无费用/审批；按完整条款提交一次通知。 |

## 托管平台边界

GitHub 仓库所有者能修改 README、Topics、About、文件与工作流，但不能通过提交一个仓库根目录的 `robots.txt`、`sitemap.xml` 或 HTML 片段来控制 `github.com` 的域名级爬虫规则、网页 `<head>` 或 Search Console 所有权。此版没有新增独立网站或 GitHub Pages，不宣称已配置网页级 canonical、JSON-LD、Open Graph 或爬虫白名单。

结构化 JSON 是项目数据，不是已注入 GitHub 网页的 schema.org 标记；`llms.txt` 也是普通仓库文件。独立站或 Pages 如将来需要，应另行配置可抓取的静态页面和真实元数据，再验证实际域名路径。

## 依据

- [Google Search Central：AI features and your website](https://developers.google.com/search/docs/appearance/ai-features)：Google AI 搜索沿用 SEO 基础；不要求特殊 AI 文件或 schema，符合条件也不保证收录或展示。
- [GitHub：Classifying your repository with topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)：Topics 可按用途、领域和语言分类，最多 20 个。
- [OpenAI：Overview of OpenAI Crawlers](https://developers.openai.com/api/docs/bots)：OAI-SearchBot 面向搜索，与训练用途的 GPTBot 分开管理；这里没有改动 GitHub 的域名爬虫策略。

## 后续怎样判断效果

定期人工记录相关查询是否能找到项目、GitHub Traffic 的访问/克隆趋势、来自用户的具体发现渠道，并保留查询日期。单次个性化搜索结果、CI 绿灯或文档提交都不证明排名增长；没有接入独立网站统计或自动持续监测。没有为此新增定时任务。
