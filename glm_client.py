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
            print(f"   - 历史总结: {len(summary)} 字符")
            print(f"   - 术语词典: {len(dict_content)} 字符")

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

        prompt = f"""你是总裁办资深董秘，负责生成管理层周例会纪要。

## ⚠️ 重要要求（必须严格遵守）

### 1. 必须完整利用历史参考
- 历史总结：共 {len(summary)} 字符，必须仔细阅读并遵循
- 术语词典：共 {len(dict_content)} 字符，必须用于纠正错别字
- 用户偏好：共 {len(preferences)} 字符，请参考用户习惯

### 2. 核心生成要求

#### 2.1 五大板块结构（必须按此顺序）
1. 每周销售进度发会议群，会上沟通销售端存在的问题及需求
2. 上周看到的人和事带给自己的思考或疑惑
3. 目前工作遇到问题需要大家群策群力的
4. 计划启动的工作需要大家提前知悉或进行意见征询的
5. TODO事项（必含表格：序号、主要事项、负责人、截止日期、状态）

#### 2.2 冷总发言处理（最高优先级）
- 完整保留所有观点、指示、总结（不得遗漏）
- 严格去口语化（删除：那个、话说、搞一下、弄一下、话说白了、就是这样、也就是说、挺、有点、嘛、哦、哈哈哈）
- 保持原始逻辑顺序（不得重新排序或重组）
- 保留商业哲理（平衡变量、回到现场、商人思维等）

#### 2.3 术语纠正（必须执行）
- 对照术语词典，纠正所有发现的错别字
- 示例：刚哥→Alter、发必达→FBA、湖南系统→图南系统

#### 2.4 存疑高亮机制（绝对禁止）
- 金额、日期、具体责任人、重要数据模糊时：使用 **[待确认：XXX]**
- 宁可留空，也不得编造
- 示例：**[待确认：具体责任人]** 负责此事项

#### 2.5 去口语化（全文执行）
- 使用正式管理语言
- 删除所有口语化表达和填充词

#### 2.6 逻辑分层
- 复杂逻辑使用 1. 2. 3. 递进
- 使用清晰的层级结构

#### 2.7 格式规范
- 使用 Markdown 格式
- 表格使用标准 Markdown 表格格式
- 加粗使用 **文本**
- 主语明确（所有 Action Items 必须有责任人）

#### 2.8 最后一行（必须）
- 另起一行，加粗写上：**撰写人：倩文**
- 不得有任何其他内容或修饰

### 3. 数据准确性要求
- 销售数据：必须明确销售额达成率、毛利额达成率、毛利率
- 时间节点：所有事项必须有明确截止日期（格式：YYYY-MM-DD）
- 责任归属：每项行动项必须有明确责任人
- 产品信息：产品名称、品类、数量必须准确

### 4. 质量控制
生成前自检：
- 是否完整保留了冷总的所有发言？
- 是否已完成术语纠正？
- 是否对模糊信息使用了存疑高亮？
- 五大板块结构是否完整？
- TODO 事项表格是否完整（序号、主要事项、负责人、截止日期、状态）？
- 最后一行格式是否正确？

## 请根据以上资料和要求生成会议纪要。"""
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
        # 计算输入数据的长度
        transcript_len = len(transcript) if transcript else 0
        notes_len = len(notes) if notes else 0

        message = f"""## 会议资料

### 录音转写稿
{transcript if transcript else '（暂无录音转写稿）'}
**字数：{{transcript_len}} 字符**

### 手写重点
{notes if notes else '（暂无手写重点）'}
**字数：{{notes_len}} 字符**

## 生成要求

### 重要提示
- 录音转写稿：{{transcript_len}} 字符，这是生成的主要依据
- 手写重点：{{notes_len}} 字符，这是补充说明和优先级指引
- 历史总结：共 {{len(summary)}} 字符，必须充分利用
- 术语词典：共 {{len(dict_content)}} 字符，必须严格遵循

### 核心任务
1. 遵循五大板块结构（销售进度、思考疑惑、问题群策、计划启动、TODO事项）
2. 严格去口语化（删除所有口语化表达）
3. 纠正所有发现的错别字（使用术语词典）
4. 对模糊信息使用存疑高亮 **[待确认：XXX]**
5. 冷总发言：完整保留、去口语化、保持逻辑顺序
6. 主语明确（所有行动项必须有责任人）
7. TODO 表格完整（序号、主要事项、负责人、截止日期、状态）
8. 最后一行必须是：**撰写人：倩文**

## 输出质量要求
- 结构清晰，逻辑连贯
- 数据准确，不编造
- 格式规范，Markdown 标准
- 充分利用历史参考的风格和格式

现在请严格按照以上要求生成完整的会议纪要。"""
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
