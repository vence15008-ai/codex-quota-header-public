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

GitHub 仓库所有者能修改 README、Topics、About、文件与工作流，但不能通过提交一个仓库根目录的 `robots.txt`、`sitemap.xml` 或 HTML 片段来控制 `github.com` 的域名级爬虫规则、网页 `<head>` 或 Search Console 所有权。

本版新增独立的 [GitHub Pages 项目网站](https://vence15008-ai.github.io/codex-quota-header-public/)，源码在 [site/index.html](../site/index.html) 和 [English page](../site/en/index.html)。正文直接输出可抓取 HTML，不依赖 JavaScript 渲染；各语言配置自引用 canonical、互相对应的 hreflang、title、description、Open Graph 和真实的 SoftwareApplication JSON-LD，不添加虚构评分或评价。页面包含 CDP 风险及许可证说明，示意数据明确标为虚构。

[部署工作流](../.github/workflows/pages.yml)通过测试后仅上传 `site/`，不把工作区、Git 历史、runtime 或本地截图放上网站。GitHub 仓库页本身未注入 schema.org 标记。

项目地址位于 `/codex-quota-header-public/` 子路径，因此没有用子目录 `robots.txt` 冒充域名根规则；有效规则位于 `https://vence15008-ai.github.io/robots.txt`，不在本项目控制范围。本站不主动限制搜索抓取，但域名规则、上游可用性及搜索平台仍可能影响实际抓取。没有擅自更改训练爬虫偏好。

网站地图位于 [sitemap.xml](https://vence15008-ai.github.io/codex-quota-header-public/sitemap.xml)，只列出中英文规范网址。Google Search Console 使用该项目完整路径的 **URL-prefix** 资源，通过首页公开的 `google-site-verification` 元标签验证；保留该标签以维持验证。验证与提交状态以 Search Console 实际结果为准，不能仅凭源码中的标记就宣称已验证或收录。此标记是公开的所有权证明，不是账号密码或 API 凭证。

提交步骤：验证资源 → “站点地图”提交完整 sitemap URL → “网址检查”检查首页并在可用时请求编入索引。没有收录保证、付费提交服务或自动反复请求。`llms.txt` 仅为可选文档索引，非官方排名协议。

## 依据

- [Google Search Central：AI features and your website](https://developers.google.com/search/docs/appearance/ai-features)：Google AI 搜索沿用 SEO 基础；不要求特殊 AI 文件或 schema，符合条件也不保证收录或展示。
- [GitHub：Classifying your repository with topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)：Topics 可按用途、领域和语言分类，最多 20 个。
- [OpenAI：Overview of OpenAI Crawlers](https://developers.openai.com/api/docs/bots)：OAI-SearchBot 面向搜索，与训练用途的 GPTBot 分开管理；这里没有改动 GitHub 的域名爬虫策略。

## 后续怎样判断效果

定期人工记录相关查询是否能找到项目、GitHub Traffic 的访问/克隆趋势、来自用户的具体发现渠道，并保留查询日期。单次个性化搜索结果、CI 绿灯或文档提交都不证明排名增长；没有接入独立网站统计或自动持续监测。没有为此新增定时任务。
