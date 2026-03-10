"""
GLM-4 API 客户端
用于调用智谱 GLM-4 模型生成会议纪要
"""

import requests
import json
from typing import Optional, Dict, Any
from pathlib import Path


class GLMClient:
    """GLM-4 API 客户端"""

    def __init__(self, api_key: str):
        """
        初始化 GLM-4 客户端

        Args:
            api_key: GLM-4 API 密钥
        """
        self.api_key = api_key
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate_minutes(self, transcript: str, notes: str, reference: Dict[str, str]) -> Optional[str]:
        """
        生成会议纪要

        Args:
            transcript: 录音转写内容
            notes: 手写重点内容
            reference: reference 文件内容字典

        Returns:
            生成的会议纪要内容
        """
        # 构建系统提示词
        system_prompt = self._build_system_prompt(reference)

        # 构建用户消息
        user_message = self._build_user_message(transcript, notes)

        # 调用 API
        try:
            print(f"🚀 开始调用 GLM-4 API...")
            print(f"📊 输入数据统计：")
            print(f"   - 录音转写: {len(transcript)} 字符")
            print(f"   - 手写重点: {len(notes)} 字符")
            print(f"   - 历史总结: {len(reference.get('01_历史纪要重点总结.md', ''))} 字符")
            print(f"   - 术语词典: {len(reference.get('02_组织与术语词典.md', ''))} 字符")

            payload = {
                "model": "glm-4",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 4096
            }

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=120  # 2分钟超时
            )

            print(f"   API 请求已发送，等待响应...")
            response.raise_for_status()
            result = response.json()

            print(f"   API 响应状态码: {response.status_code}")

            # 提取生成的内容
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"✅ API 调用成功，生成 {len(content)} 字符")
                return content

            print(f"❌ API 响应格式错误: {result}")
            return None

        except requests.exceptions.Timeout:
            print("⏱️ GLM-4 API 请求超时（2分钟）")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"❌ GLM-4 API HTTP 错误: {e}")
            print(f"   HTTP 状态码: {e.response.status_code if e.response else '未知'}")
            print(f"   响应内容: {e.response.text[:500] if e.response else '无'}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ GLM-4 API 请求异常: {e}")
            return None
        except Exception as e:
            print(f"❌ GLM-4 API 调用出错: {e}")
            print(f"   错误类型: {type(e).__name__}")
            return None

    def _build_system_prompt(self, reference: Dict[str, str]) -> str:
        """
        构建系统提示词

        Args:
            reference: reference 文件内容

        Returns:
            系统提示词
        """
        summary = reference.get('01_历史纪要重点总结.md', '')
        dict_content = reference.get('02_组织与术语词典.md', '')
        preferences = reference.get('03_用户偏好.json', '{}')
        style_template = reference.get('04_风格模板.md', '')

        # 从风格模板中提取具体的风格要求
        style_requirements = self._extract_style_requirements(style_template)

        prompt = f"""你是总裁办资深董秘，负责生成管理层周例会纪要。你的写作风格必须严格模仿用户的写作特点。

## ⚠️ 写作风格要求（最高优先级）

以下是从用户的会议纪要中学习到的写作风格特点，**必须严格遵守**：

### 1. 措辞特点
{style_requirements.get('措辞特点', '使用正式管理语言，避免口语化表达')}

### 2. 句子结构
{style_requirements.get('句子结构', '使用清晰的句子结构，长短句交替使用')}

### 3. 表达习惯
{style_requirements.get('表达习惯', '表达要准确、简洁，符合管理规范')}

### 4. 重点强调方式
{style_requirements.get('重点强调', '重要信息使用加粗，关键数据要突出')}

### 5. 格式偏好
{style_requirements.get('格式偏好', '遵循 Markdown 格式规范，使用清晰的层级结构')}

### 6. 特殊表达
{style_requirements.get('特殊表达', '如果有固定的开场白或结束语，请遵循')}

---

## 核心生成要求

### 1. 必须完整利用历史参考
- 历史总结：共 {len(summary)} 字符，必须仔细阅读并遵循
- 术语词典：共 {len(dict_content)} 字符，必须用于纠正错别字
- 用户偏好：共 {len(preferences)} 字符，请参考用户习惯
- 风格模板：共 {len(style_template)} 字符，**上述写作风格要求必须严格遵循**

### 2. 五大板块结构（必须按此顺序）
1. 每周销售进度发会议群，会上沟通销售端存在的问题及需求
2. 上周看到的人和事带给自己的思考或疑惑
3. 目前工作遇到问题需要大家群策群力的
4. 计划启动的工作需要大家提前知悉或进行意见征询的
5. TODO事项（必含表格：序号、主要事项、负责人、截止日期、状态）

### 3. 冷总发言处理（最高优先级）
- 完整保留所有观点、指示、总结（不得遗漏）
- 严格去口语化（删除：那个、话说、搞一下、弄一下、话说白了、就是这样、也就是说、挺、有点、嘛、哦、哈哈哈）
- 保持原始逻辑顺序（不得重新排序或重组）
- **重要：必须应用上述写作风格特点中的表达方式**

### 4. 术语纠正（必须执行）
- 对照术语词典，纠正所有发现的错别字
- 示例：刚哥→Alter、发必达→FBA、湖南系统→图南系统

### 5. 存疑高亮机制（绝对禁止）
- 金额、日期、具体责任人、重要数据模糊时：使用 **[待确认：XXX]**
- 宁可留空，也不得编造

### 6. 最后一行（必须）
- 另起一行，加粗写上：**撰写人：倩文**

---

## 质量控制

生成前自检：
- ✅ 是否严格应用了写作风格特点（措辞、句子结构、表达习惯）？
- ✅ 是否完整保留了冷总的所有发言？
- ✅ 是否已完成术语纠正？
- ✅ 是否对模糊信息使用了存疑高亮？
- ✅ 五大板块结构是否完整？
- ✅ TODO 表格是否完整（序号、主要事项、负责人、截止日期、状态）？
- ✅ 最后一行格式是否正确？

现在请根据以上风格要求和生成规则生成会议纪要。"""

        return prompt

    def _extract_style_requirements(self, style_template: str) -> Dict[str, str]:
        """
        从风格模板中提取具体的风格要求

        Args:
            style_template: 风格模板内容

        Returns:
            风格要求字典
        """
        requirements = {
            "措辞特点": "使用正式管理语言，避免口语化表达",
            "句子结构": "使用清晰的句子结构，长短句交替使用",
            "表达习惯": "表达要准确、简洁，符合管理规范",
            "重点强调": "重要信息使用加粗，关键数据要突出",
            "格式偏好": "遵循 Markdown 格式规范，使用清晰的层级结构",
            "特殊表达": "遵循用户的固定表达方式"
        }

        # 从风格模板中提取具体要求
        if "措辞特点" in style_template:
            start = style_template.find("### 1. 措辞特点")
            end = style_template.find("### 2.", start)
            if end == -1:
                end = len(style_template)
            content = style_template[start:end].replace("### 1. 措辞特点", "").strip()
            if content:
                requirements["措辞特点"] = content

        if "句子结构" in style_template:
            start = style_template.find("### 2. 句子结构")
            end = style_template.find("### 3.", start)
            if end == -1:
                end = len(style_template)
            content = style_template[start:end].replace("### 2. 句子结构", "").strip()
            if content:
                requirements["句子结构"] = content

        if "表达习惯" in style_template:
            start = style_template.find("### 3. 表达习惯")
            end = style_template.find("### 4.", start)
            if end == -1:
                end = len(style_template)
            content = style_template[start:end].replace("### 3. 表达习惯", "").strip()
            if content:
                requirements["表达习惯"] = content

        if "重点强调" in style_template:
            start = style_template.find("### 4. 重点强调")
            end = style_template.find("### 5.", start)
            if end == -1:
                end = len(style_template)
            content = style_template[start:end].replace("### 4. 重点强调", "").strip()
            if content:
                requirements["重点强调"] = content

        if "格式偏好" in style_template:
            start = style_template.find("### 5. 格式偏好")
            end = style_template.find("### 6.", start)
            if end == -1:
                end = len(style_template)
            content = style_template[start:end].replace("### 5. 格式偏好", "").strip()
            if content:
                requirements["格式偏好"] = content

        if "特殊表达" in style_template:
            start = style_template.find("### 6. 特殊表达")
            end = style_template.find("### 7.", start)
            if end == -1:
                end = len(style_template)
            content = style_template[start:end].replace("### 6. 特殊表达", "").strip()
            if content:
                requirements["特殊表达"] = content

        return requirements
