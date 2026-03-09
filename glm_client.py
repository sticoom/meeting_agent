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

            response.raise_for_status()
            result = response.json()

            # 提取生成的内容
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']

            return None

        except requests.exceptions.Timeout:
            print("GLM-4 API 请求超时")
            return None
        except requests.exceptions.RequestException as e:
            print(f"GLM-4 API 请求失败: {e}")
            return None
        except Exception as e:
            print(f"GLM-4 API 调用出错: {e}")
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

        prompt = f"""你是总裁办资深董秘，负责生成管理层周例会纪要。

## 核心要求

1. **严格按照 skill.md 中的规范生成纪要**
2. **冷总发言优先处理**：
   - 完整保留所有观点、指示、总结
   - 严格去口语化（那个、话说、搞一下、弄一下等）
   - 保持原始逻辑顺序
   - 保留商业哲理（平衡变量、回到现场、商人思维等）

3. **术语纠正**：对照术语词典，纠正机器转写的错别字

4. **存疑高亮机制**：对于金额、日期、责任人模糊不清的信息，使用 **[待确认：具体内容]** 标注，绝对不准瞎编

5. **五大板块结构**：
   - 每周销售进度发会议群，会上沟通销售端存在的问题及需求
   - 上周看到的人和事带给自己的思考或疑惑
   - 目前工作遇到问题需要大家群策群力的
   - 计划启动的工作需要大家提前知悉或进行意见征询的
   - TODO事项（必含表格：序号、主要事项、负责人、截止日期、状态）

6. **最后一行必须是**：**撰写人：倩文**

## 历史参考

### 历史纪要重点总结（最近要点）
{summary[:2000] if summary else '暂无历史总结'}

### 术语词典（纠正规则）
{dict_content[:2000] if dict_content else '暂无术语词典'}

### 用户偏好
{preferences[:500] if preferences else '暂无用户偏好'}

## 输出格式要求

- 使用 Markdown 格式
- 复杂逻辑使用 1. 2. 3. 递进
- 表格使用标准 Markdown 表格格式
- 加粗使用 **文本**
- 最后一行另起一行，加粗写上：**撰写人：倩文**

请严格按照以上要求生成会议纪要。"""
        return prompt

    def _build_user_message(self, transcript: str, notes: str) -> str:
        """
        构建用户消息

        Args:
            transcript: 录音转写内容
            notes: 手写重点内容

        Returns:
            用户消息
        """
        message = f"""## 会议资料

### 录音转写稿
{transcript}

### 手写重点
{notes if notes else '（无手写重点）'}

## 要求

请根据以上资料生成符合规范的《管理层周例会纪要》。
- 参考历史纪要的风格和格式
- 使用术语词典纠正错别字
- 严格去口语化
- 冷总发言要完整保留，去口语化，保持逻辑顺序
- 对模糊信息使用存疑高亮
- 必须包含五大板块和 TODO 事项表格
- 最后一行必须是：**撰写人：倩文**

现在开始生成会议纪要。"""
        return message

    def test_connection(self) -> bool:
        """
        测试 API 连接

        Returns:
            连接是否成功
        """
        try:
            payload = {
                "model": "glm-4",
                "messages": [{"role": "user", "content": "测试连接"}],
                "max_tokens": 10
            }

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )

            return response.status_code == 200

        except Exception:
            return False


def create_glm_client(api_key: Optional[str] = None) -> Optional[GLMClient]:
    """
    创建 GLM-4 客户端

    Args:
        api_key: API 密钥（如果为 None，从环境变量读取）

    Returns:
        GLM-4 客户端实例，如果配置不完整返回 None
    """
    import os

    if not api_key:
        api_key = os.getenv("GLM_API_KEY")

    if not api_key:
        return None

    return GLMClient(api_key)
