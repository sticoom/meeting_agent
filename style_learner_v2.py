"""
深度风格学习模块 V2
深度分析最终版会议纪要，提取写作风格、措辞特点、表达方式等
"""

import requests
import json
from typing import Dict, Optional, List
from glm_client import GLMClient


class DeepStyleLearner:
    """深度风格学习器"""

    def __init__(self, glm_client: GLMClient):
        """
        初始化深度风格学习器

        Args:
            glm_client: GLM-4 客户端实例
        """
        self.client = glm_client

    def extract_writing_style(self, final_minutes: str, draft_minutes: str = "") -> Dict[str, any]:
        """
        深度分析会议纪要的写作风格

        Args:
            final_minutes: 最终版会议纪要
            draft_minutes: 初稿会议纪要（可选，用于对比分析学习用户的修改习惯）

        Returns:
            包含深度风格分析的字典
        """
        prompt = self._build_deep_analysis_prompt(final_minutes, draft_minutes)

        try:
            print(f"🧠 开始深度分析会议纪要写作风格...")
            print(f"   - 会议纪要长度: {len(final_minutes)} 字符")
            if transcript:
                print(f"   - 录音转写长度: {len(transcript)} 字符")

            # 调用 GLM-4 API
            payload = {
                "model": "glm-4",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是资深语言风格分析师，擅长分析中文商务写作风格、措辞特点、表达方式、句子结构等。"
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 4000
            }

            response = requests.post(
                self.client.base_url,
                headers=self.client.headers,
                json=payload,
                timeout=90
            )

            response.raise_for_status()
            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"✅ 风格分析完成，生成 {len(content)} 字符")

                # 解析返回的内容
                return self._parse_deep_analysis(content)

            print(f"❌ API 响应格式错误: {result}")
            return self._empty_analysis()

        except Exception as e:
            print(f"❌ 深度风格分析失败: {e}")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误详情: {str(e)}")
            return self._empty_analysis()

    def extract_new_terms(self, final_minutes: str, existing_terms: str = "") -> List[Dict[str, str]]:
        """
        从会议纪要中提取新术语

        Args:
            final_minutes: 最终版会议纪要
            existing_terms: 现有术语词典内容

        Returns:
            新术语列表，包含 [错误称呼, 正式称呼, 备注]
        """
        prompt = self._build_term_extraction_prompt(final_minutes, existing_terms)

        try:
            print(f"📖 开始提取新术语...")
            print(f"   - 会议纪要长度: {len(final_minutes)} 字符")
            print(f"   - 现有词典长度: {len(existing_terms)} 字符")

            payload = {
                "model": "glm-4",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是术语提取专家，擅长从会议纪要中识别组织名称、人名、产品名、业务术语等，并判断其正式称呼。"
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 2000
            }

            response = requests.post(
                self.client.base_url,
                headers=self.client.headers,
                json=payload,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"✅ 术语提取完成，生成 {len(content)} 字符")

                return self._parse_new_terms(content)

            return []

        except Exception as e:
            print(f"❌ 术语提取失败: {e}")
            return []

    def extract_user_preferences(self, final_minutes: List[str]) -> Dict[str, str]:
        """
        分析多篇会议纪要，提取用户偏好

        Args:
            final_minutes: 多篇最终版会议纪要的列表

        Returns:
            用户偏好字典
        """
        if len(final_minutes) < 2:
            print("⚠️ 会议纪要少于2篇，无法准确分析用户偏好")
            return self._empty_preferences()

        prompt = self._build_preferences_analysis_prompt(final_minutes)

        try:
            print(f"🎯 开始分析用户写作偏好...")
            print(f"   - 分析纪要数量: {len(final_minutes)} 篇")

            payload = {
                "model": "glm-4",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是用户偏好分析专家，擅长从多篇会议纪要中识别写作习惯、格式偏好、内容重点等。"
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 3000
            }

            response = requests.post(
                self.client.base_url,
                headers=self.client.headers,
                json=payload,
                timeout=90
            )

            response.raise_for_status()
            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"✅ 偏好分析完成，生成 {len(content)} 字符")

                return self._parse_preferences(content)

            return self._empty_preferences()

        except Exception as e:
            print(f"❌ 偏好分析失败: {e}")
            return self._empty_preferences()

    def generate_style_guide(self, style_analysis: Dict[str, any]) -> str:
        """
        根据风格分析生成写作指南

        Args:
            style_analysis: 深度风格分析结果

        Returns:
            写作指南文本
        """
        if not style_analysis.get("措辞特点") and not style_analysis.get("句子结构"):
            return ""

        # 统计有多少维度已完成学习
        learned_count = sum(1 for k, v in style_analysis.items() if v and v != "待学习")

        guide = f"""
## 写作风格指南

> 📊 **学习进度**: {learned_count}/6 个维度已完成学习

---

### 1. 措辞特点
{style_analysis.get('措辞特点', '待学习')}

---

### 2. 句子结构
{style_analysis.get('句子结构', '待学习')}

---

### 3. 表达习惯
{style_analysis.get('表达习惯', '待学习')}

---

### 4. 重点强调方式
{style_analysis.get('重点强调', '待学习')}

---

### 5. 格式偏好
{style_analysis.get('格式偏好', '待学习')}

---

### 6. 特殊表达
{style_analysis.get('特殊表达', '待学习')}
"""

        return guide

    def _build_deep_analysis_prompt(self, final_minutes: str, draft_minutes: str = "") -> str:
        """构建深度分析提示词"""
        # 限制长度，避免超出 token 限制
        final_preview = final_minutes[:7000] if len(final_minutes) > 7000 else final_minutes

        # 对比分析部分
        comparison_section = ""
        if draft_minutes and len(draft_minutes) > 100:
            draft_preview = draft_minutes[:4000] if len(draft_minutes) > 4000 else draft_minutes
            comparison_section = f"""

## 对比参考材料

请对比最终版纪要与初稿，分析用户是如何修改和优化的：

### 初稿参考
```
{draft_preview}
```

### 对比分析重点
- 用户删除了哪些口语化表达？如何替换的？
- 用户新增了哪些正式表达？
- 用户如何重新组织信息的？
- 用户如何处理冷总发言的？
- 用户对数据和重点信息的呈现方式有哪些改进？
"""

        prompt = f"""请深度分析以下会议纪要的写作风格，提取以下维度的详细信息：

## 最终版会议纪要
```
{final_preview}
```
{comparison_section}
## 分析要求

请从以下维度深度分析这篇会议纪要的写作风格。如果提供了初稿，请通过对比分析用户的修改习惯：

### 1. 措辞特点（重要）
- 使用的词汇特点（正式/半正式/口语化程度，给出判断依据）
- 常用的高级表达和措辞（列出具体词汇）
- 哪些词汇是偏好使用的（给出频率高的词汇）
- 哪些词汇是避免使用的（说明原因）
- 具体的用词示例（至少 5 个真实示例）

### 2. 句子结构（重要）
- 句子的长短特点（短句/中长句/长句比例，给出统计）
- 句子结构的偏好（简单句/复合句/复杂句的使用比例）
- 段落组织方式（平均每段字数）
- 逻辑连接词的使用习惯（列出常用的连接词）
- 具体的句子结构示例（至少 3 个真实示例）

### 3. 表达习惯（重要）
- 冷总发言的处理方式（直接引用/转述/总结，给出示例）
- 普通信息的表达方式（数据、时间、责任人的表述习惯）
- 数据呈现的习惯（表格/文字/混合，示例）
- 时间表述的方式（具体格式）
- 责任人表述的方式（格式特点）
- 具体的表达示例（至少 3 个真实示例）

### 4. 重点强调方式（重要）
- 如何强调重要信息（加粗、特殊格式、独立段落等，示例）
- 关键数据的呈现方式（数字、百分比、表格）
- 优先级的表达方式（如何标记紧急/重要）
- 冷总指示的强调方式（特殊格式）
- 具体的强调示例（至少 3 个真实示例）

### 5. 格式偏好
- 五大板块的具体结构（各板块的字数比例）
- 标题层级的使用习惯（#、##、### 的使用规则）
- 列表的使用方式（有序/无序列表的偏好）
- 表格的格式偏好（列数、对齐方式）
- 特殊格式的使用（分割线、引用等）

### 6. 特殊表达（重要）
- 是否有独特的表达方式或口头禅（如果有，列出）
- 是否有固定的开场白或结束语（原文引用）
- 是否有特殊的连接词（列出）
- 是否有特定的标点使用习惯（说明）
- 具体的特殊表达示例（至少 3 个真实示例）

## 输出格式要求（严格执行）

**必须严格按照以下 JSON 格式返回，不要包含任何其他文本：**

```json
{{
  "措辞特点": "详细的措辞特点描述，包含具体用词示例",
  "句子结构": "详细的句子结构描述，包含具体示例",
  "表达习惯": "详细的表达习惯描述，包含具体示例",
  "重点强调": "详细的重点强调方式描述，包含具体示例",
  "格式偏好": "详细的格式偏好描述，包含具体示例",
  "特殊表达": "详细的特殊表达描述，包含具体示例"
}}
```

**重要提示：**
1. 只返回 JSON 对象，不要包含任何解释性文字
2. 每个字段的值必须是完整的描述，包含真实示例
3. 如果某个维度没有明显特征，请说明"无明显特点"
4. 示例必须来自原文，不要编造

现在请开始深度分析并返回 JSON 格式的结果。"""

        return prompt

    def _build_term_extraction_prompt(self, final_minutes: str, existing_terms: str = "") -> str:
        """构建术语提取提示词"""
        final_preview = final_minutes[:5000] if len(final_minutes) > 5000 else final_minutes

        existing_section = f"\n\n## 现有术语词典\n\n{existing_terms}\n\n" if existing_terms else ""

        prompt = f"""请从以下会议纪要中提取新术语：

## 会议纪要
```
{final_preview}
```
{existing_section}
## 提取要求

请从会议纪要中识别以下内容：

### 1. 组织名称
- 提取所有组织、部门、团队名称
- 判断正式称呼
- 判断是否为口语化或错误称呼

### 2. 人员名称
- 提取所有人员姓名
- 判断正式称呼
- 判断是否为口语化或错误称呼（如"刚哥"→"Alter"）

### 3. 产品名称
- 提取所有产品、服务、系统名称
- 判断正式称呼

### 4. 业务术语
- 提取所有业务相关的专业术语
- 判断正式称呼

## 输出格式要求

请严格按照以下格式返回：

| 类型 | 错误/口语称呼 | 正式称呼 | 备注 |
|------|--------------|----------|------|
| 组织 | [示例] | [示例] | [说明] |
| 人员 | [示例] | [示例] | [说明] |
| 产品 | [示例] | [示例] | [说明] |
| 术语 | [示例] | [示例] | [说明] |

只返回新发现的术语，不要包含词典中已有的术语。如果没有发现新术语，返回空表格。

现在请开始提取。"""

        return prompt

    def _build_preferences_analysis_prompt(self, final_minutes: List[str]) -> str:
        """构建偏好分析提示词"""
        # 选择最近 3 篇会议纪要进行分析
        selected_minutes = final_minutes[-3:]
        minutes_content = "\n\n---\n\n".join([f"## 会议纪要 {i+1}\n\n{m[:4000]}" for i, m in enumerate(selected_minutes)])

        prompt = f"""请分析以下多篇会议纪要，提取用户的写作偏好：

## 会议纪要（共 {len(selected_minutes)} 篇）

{minutes_content}

## 分析要求

请从以下维度分析用户的写作偏好：

### 1. 五大板块的处理方式
- 每个板块的篇幅比例
- 板块内容的详细程度
- 板块的组织方式

### 2. 冷总发言的处理偏好
- 是否完整保留冷总发言
- 冷总发言的表达方式（直接引用/转述/总结）
- 冷总重要指示的强调方式

### 3. 数据呈现偏好
- 数据的呈现方式（表格/文字/混合）
- 数据的详细程度
- 数据的强调方式

### 4. TODO 事项的偏好
- TODO 表格的详细程度
- 负责人表述的方式
- 截止日期的格式
- 状态描述的方式

### 5. 语言风格偏好
- 整体语言风格（正式/半正式/口语化）
- 句子长短偏好
- 用词偏好

### 6. 格式偏好
- 标题层级使用习惯
- 列表使用习惯
- 加粗使用习惯
- 段落组织习惯

## 输出格式要求

请按照以下格式返回：

### 板块处理
[详细的板块处理偏好]

### 冷总发言处理
[详细的冷总发言处理偏好]

### 数据呈现
[详细的数据呈现偏好]

### TODO 事项
[详细的 TODO 事项处理偏好]

### 语言风格
[详细的语言风格偏好]

### 格式偏好
[详细的格式偏好]

现在请开始分析。"""

        return prompt

    def _parse_deep_analysis(self, content: str) -> Dict[str, str]:
        """解析深度分析内容"""
        # 尝试解析 JSON 格式
        import re

        # 查找 JSON 对象
        json_match = re.search(r'\{[\s\S]*\}', content)

        if json_match:
            try:
                import json
                # 清理 JSON 字符串（移除可能的 markdown 代码块标记）
                json_str = json_match.group(0).strip()
                json_str = json_str.replace('```json', '').replace('```', '')

                analysis_dict = json.loads(json_str)

                # 验证并补充缺失的字段
                required_keys = ["措辞特点", "句子结构", "表达习惯", "重点强调", "格式偏好", "特殊表达"]
                for key in required_keys:
                    if key not in analysis_dict or not analysis_dict[key]:
                        analysis_dict[key] = "待学习"

                print(f"✅ JSON 解析成功，提取了 {len([k for k in analysis_dict if analysis_dict[k] != '待学习'])} 个维度的信息")

                return analysis_dict

            except json.JSONDecodeError as e:
                print(f"⚠️ JSON 解析失败，尝试文本解析: {e}")
                # JSON 解析失败，继续使用文本解析
            except Exception as e:
                print(f"⚠️ 解析出错: {e}")

        # 回退到文本解析（兼容旧格式）
        analysis = {
            "措辞特点": "",
            "句子结构": "",
            "表达习惯": "",
            "重点强调": "",
            "格式偏好": "",
            "特殊表达": ""
        }

        lines = content.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("### 措辞特点"):
                current_section = "措辞特点"
            elif line.startswith("### 句子结构"):
                current_section = "句子结构"
            elif line.startswith("### 表达习惯"):
                current_section = "表达习惯"
            elif line.startswith("### 重点强调"):
                current_section = "重点强调"
            elif line.startswith("### 格式偏好"):
                current_section = "格式偏好"
            elif line.startswith("### 特殊表达"):
                current_section = "特殊表达"
            elif (line.startswith("- ") or line.startswith("• ") or line.startswith("* ")) and current_section:
                if analysis[current_section]:
                    analysis[current_section] += "\n"
                analysis[current_section] += line

        # 如果某项为空，标记为待学习
        for key in analysis:
            if not analysis[key]:
                analysis[key] = "待学习"

        return analysis

    def _parse_new_terms(self, content: str) -> List[Dict[str, str]]:
        """解析新术语内容"""
        terms = []

        lines = content.split('\n')
        in_table = False

        for line in lines:
            line = line.strip()

            if '|' in line and not line.startswith('|---'):
                parts = [p.strip() for p in line.split('|')]

                # 跳过表头
                if len(parts) >= 4 and parts[0] != "类型":
                    terms.append({
                        "type": parts[0],
                        "wrong": parts[1],
                        "correct": parts[2],
                        "note": parts[3] if len(parts) > 3 else ""
                    })

        return terms

    def _parse_preferences(self, content: str) -> Dict[str, str]:
        """解析偏好分析内容"""
        preferences = {
            "板块处理": "",
            "冷总发言处理": "",
            "数据呈现": "",
            "TODO 事项": "",
            "语言风格": "",
            "格式偏好": ""
        }

        lines = content.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("### 板块处理"):
                current_section = "板块处理"
            elif line.startswith("### 冷总发言处理"):
                current_section = "冷总发言处理"
            elif line.startswith("### 数据呈现"):
                current_section = "数据呈现"
            elif line.startswith("### TODO 事项"):
                current_section = "TODO 事项"
            elif line.startswith("### 语言风格"):
                current_section = "语言风格"
            elif line.startswith("### 格式偏好"):
                current_section = "格式偏好"
            elif line.startswith("- ") and current_section:
                if preferences[current_section]:
                    preferences[current_section] += "\n"
                preferences[current_section] += line

        return preferences

    def _empty_analysis(self) -> Dict[str, str]:
        """返回空的分析结果"""
        return {
            "措辞特点": "分析失败，待学习",
            "句子结构": "分析失败，待学习",
            "表达习惯": "分析失败，待学习",
            "重点强调": "分析失败，待学习",
            "格式偏好": "分析失败，待学习",
            "特殊表达": "分析失败，待学习"
        }

    def _empty_preferences(self) -> Dict[str, str]:
        """返回空的偏好结果"""
        return {
            "板块处理": "分析失败，待学习",
            "冷总发言处理": "分析失败，待学习",
            "数据呈现": "分析失败，待学习",
            "TODO 事项": "分析失败，待学习",
            "语言风格": "分析失败，待学习",
            "格式偏好": "分析失败，待学习"
        }


def update_summary_with_style(summary: str, style_guide: str) -> str:
    """
    用风格指南更新历史纪要重点总结

    Args:
        summary: 现有总结内容
        style_guide: 新的风格指南

    Returns:
        更新后的总结
    """
    from datetime import datetime

    new_entry = f"""

---

## {datetime.now().strftime('%Y-%m-%d')} 风格学习记录

### 新发现的写作风格
{style_guide}

---

"""

    updated_summary = new_entry + summary if summary else new_entry
    return updated_summary


def update_terms_dict(existing_dict: str, new_terms: List[Dict[str, str]]) -> str:
    """
    用新术语更新术语词典

    Args:
        existing_dict: 现有词典内容
        new_terms: 新术语列表

    Returns:
        更新后的词典
    """
    if not new_terms:
        return existing_dict

    new_terms_section = "\n\n## 新增术语（自动学习）\n\n"
    new_terms_section += "| 类型 | 错误/口语称呼 | 正式称呼 | 备注 |\n"
    new_terms_section += "|------|--------------|----------|------|\n"

    for term in new_terms:
        new_terms_section += f"| {term['type']} | {term['wrong']} | {term['correct']} | {term['note']} |\n"

    return existing_dict + new_terms_section


def update_user_preferences(existing_preferences: str, new_preferences: Dict[str, str]) -> str:
    """
    用新偏好更新用户偏好文件

    Args:
        existing_preferences: 现有偏好内容（JSON 字符串）
        new_preferences: 新偏好字典

    Returns:
        更新后的偏好内容（JSON 字符串）
    """
    try:
        import json

        # 解析现有偏好
        existing_dict = json.loads(existing_preferences) if existing_preferences else {}
    except:
        existing_dict = {}

    # 更新偏好
    existing_dict.update(new_preferences)

    # 标记更新时间
    existing_dict["last_updated"] = datetime.now().isoformat()

    return json.dumps(existing_dict, ensure_ascii=False, indent=2)
