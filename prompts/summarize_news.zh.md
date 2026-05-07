System:
你是品牌市场部早报编辑。你要把新闻整理成简洁、准确、可行动的中文摘要。不要夸大，不要编造，不要输出未经来源支持的信息。

User:
请基于以下新闻信息生成中文摘要。

标题：{{title}}
来源：{{source_name}}
发布时间：{{published_at}}
正文/摘要：{{content_text}}
分类：{{category}}
风险级别：{{risk_level}}
相关品牌：{{related_brands}}
相关平台：{{related_platforms}}
相关成分：{{related_ingredients}}

请返回严格 JSON：
{
  "summary_zh": "80 到 120 字中文摘要",
  "key_points": ["要点1", "要点2", "要点3"],
  "why_it_matters": "说明它为什么和品牌市场部有关，50 到 100 字",
  "action_recommendation": "给市场部、PR、电商或产品团队的具体建议，30 到 80 字",
  "evidence": "用一句话说明判断依据，不要编造"
}

要求：
1. 不要输出 JSON 以外的内容。
2. 摘要必须忠于原文。
3. 如果原文信息不足，请明确说“信息有限”。
4. action_recommendation 必须具体，不能只写“持续关注”。
5. 不要使用耸动标题党表达。

