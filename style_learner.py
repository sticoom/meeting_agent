"""
风格学习模块
对比初稿和最终稿，提取风格学习内容
"""

import json
from typing import Dict, Optional
from glm_client import GLMClient


class StyleLearner:
    """风格学习器"""

    def __init__(self, glm_client: GLMClient):
        """
        初始化风格学习器

        Args:
            glm_client: GLM-4 客户端实例
        """
        self.client = glm_client

    def extract_style_from_comparison(self, draft: str, final: str) -> Dict[str, str]:
        """
        对比初稿和最终稿，提取风格学习内容

        Args:
            draft: 初稿内容
            final: 最终稿内容

        Returns:
            学习记录字典，包含修改要点、风格规则、更新的模板内容
        """
        prompt = self._build_comparison_prompt(draft, final)

        try:
            print(f"🤖 开始分析初稿和最终稿的差异...")
            print(f"   - 初稿长度: {len(draft)} 字符")
            print(f"   - 最终稿长度: {len(final)} 字符")

            # 调用 GLM-4 API
            payload = {
                "model": "glm-4",
                "messages": [
                    {"role": "system", "content": "你是会议纪要风格分析专家，负责对比初稿和最终稿，提取用户的写作风格偏好。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,  # 较低的温度，确保提取准确
                "max_tokens": 2000
            }

            response = self.client.requests.post(
                self.client.base_url,
                headers=self.client.headers,
                json=payload,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"✅ 风格分析完成，生成 {len(content)} 字符")

                # 解析返回的内容
                return self._parse_learning_content(content)

            print(f"❌ API 响应格式错误: {result}")
            return self._empty_learning_record()

        except Exception as e:
            print(f"❌ 风格分析失败: {e}")
            return self._empty_learning_record()

    def _build_comparison_prompt(self, draft: str, final: str) -> str:
        """
        构建对比分析的提示词

        Args:
            draft: 初稿内容
            final: 最终稿内容

        Returns:
            提示词
        """
        # 限制长度，避免超出 token 限制
        draft_preview = draft[:4000] if len(draft) > 4000 else draft
        final_preview = final[:4000] if len(final) > 4000 else final

        prompt = f"""请对比以下会议纪要的初稿和最终稿，提取用户修改背后的风格规则。

## 初稿
```
{draft_preview}
```

## 最终稿
```
{final_preview}
```

## 提取要求

请分析并提取以下内容：

### 1. 用户修改要点
列出用户在最终稿中修改的主要内容，例如：
- 增加了哪些内容？
- 删除了哪些内容？
- 调整了哪些结构？
- 修改了哪些表达方式？

### 2. 发现的风格规则
从用户的修改中提取风格规则，例如：
- 标题格式要求
- 段落组织方式
- 冷总发言的处理风格
- 数据呈现方式
- TODO 表格的具体格式
- 语言表达的偏好

### 3. 更新的模板内容
指出哪些内容应该更新到会议纪要风格模板中，例如：
- 新增的格式要求
- 特殊的表达方式
- 表格的详细格式
- 任何结构上的变化

## 输出格式要求

请严格按照以下格式返回（不要添加其他内容）：

### 用户修改要点
- [要点1]
- [要点2]
- ...

### 发现的风格规则
- [规则1]
- [规则2]
- ...

### 更新的模板内容
- [需要更新的内容1]
- [需要更新的内容2]
- ...

现在请开始分析。"""

        return prompt

    def _parse_learning_content(self, content: str) -> Dict[str, str]:
        """
        解析学习内容

        Args:
            content: GLM-4 返回的内容

        Returns:
            解析后的学习记录字典
        """
        learning_record = {
            "user_modifications": "",
            "style_rules": "",
            "template_updates": ""
        }

        lines = content.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("### 用户修改要点"):
                current_section = "user_modifications"
            elif line.startswith("### 发现的风格规则"):
                current_section = "style_rules"
            elif line.startswith("### 更新的模板内容"):
                current_section = "template_updates"
            elif line.startswith("- ") and current_section:
                if learning_record[current_section]:
                    learning_record[current_section] += "\n"
                learning_record[current_section] += line

        return learning_record

    def _empty_learning_record(self) -> Dict[str, str]:
        """
        返回空的学习记录

        Returns:
            空的学习记录字典
        """
        return {
            "user_modifications": "提取失败，无法获取用户修改要点",
            "style_rules": "提取失败，无法获取风格规则",
            "template_updates": "提取失败，无法获取更新内容"
        }


def update_style_template(learning_record: Dict[str, str], current_template: str = "") -> str:
    """
    更新风格模板

    Args:
        learning_record: 学习记录字典
        current_template: 当前的风格模板内容

    Returns:
        更新后的风格模板内容
    """
    from datetime import datetime

    # 如果没有当前模板，创建初始模板
    if not current_template:
        current_template = """# 会议纪要最佳风格模板

本模板从多次学习中提取，持续优化中。

## 标题格式
# 管理层周例会纪要
时间：YYYY-MM-DD

---

## 五大板块结构
[从学习中提取的结构]

---

## 冷总发言处理方式
[从学习中提取的处理规则]

---

## TODO 表格格式
| 序号 | 主要事项 | 负责人 | 截止日期 | 状态 |
|------|----------|---------|----------|------|

---

## 写作风格要点
[从学习中提取的风格要点]
"""

    # 更新模板内容
    updated_template = current_template

    # 添加新的学习记录
    if learning_record.get("style_rules") and learning_record["style_rules"] != "提取失败，无法获取风格规则":
        # 在写作风格要点部分添加新规则
        if "写作风格要点" in updated_template:
            updated_template = updated_template.replace(
                "## 写作风格要点\n[从学习中提取的风格要点]",
                f"## 写作风格要点\n{learning_record['style_rules']}"
            )

        # 添加更新记录
        update_log = f"""

---

## {datetime.now().strftime('%Y-%m-%d')} 学习更新

### 用户修改要点
{learning_record['user_modifications']}

### 新增的风格规则
{learning_record['style_rules']}

### 建议的模板更新
{learning_record['template_updates']}
"""

        updated_template = updated_template + update_log

    return updated_template


def append_to_learning_log(learning_record: Dict[str, str]) -> bool:
    """
    将学习记录追加到学习日志文件

    Args:
        learning_record: 学习记录字典

    Returns:
        是否成功
    """
    from datetime import datetime
    from pathlib import Path

    try:
        log_file = Path("reference/03_风格学习记录.md")
        log_file.parent.mkdir(exist_ok=True)

        # 读取现有日志
        existing_log = ""
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                existing_log = f.read()

        # 准备新的学习记录
        new_record = f"""
---

## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 学习记录

### 用户修改要点
{learning_record['user_modifications']}

### 发现的风格规则
{learning_record['style_rules']}

### 更新的模板内容
{learning_record['template_updates']}

---

"""

        # 更新日志文件
        updated_log = new_record + existing_log

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(updated_log)

        print(f"✅ 学习记录已保存到: {log_file}")
        return True

    except Exception as e:
        print(f"❌ 保存学习记录失败: {e}")
        return False
