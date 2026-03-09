"""
会议纪要生成 Agent - Streamlit 小程序
页面简洁美观，支持对话式修改 Skill
"""

import os
import json
import io
from datetime import datetime
from pathlib import Path

import streamlit as st
from docx import Document
from docx.shared import Inches

# GitHub 管理模块
from github_manager import GitHubManager, create_github_manager, is_github_mode

# GLM-4 客户端
from glm_client import GLMClient, create_glm_client

# 页面配置
st.set_page_config(
    page_title="会议纪要生成 Agent",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    /* 主容器样式 */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        padding: 2rem 0;
    }

    /* 章节标题样式 */
    .section-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #3B82F6;
        padding: 1rem 0;
        border-bottom: 2px solid #E5E7EB;
    }

    /* 输入框样式 */
    .stTextArea > div > div > textarea {
        border: 2px solid #D1D5DB;
        border-radius: 8px;
        padding: 1rem;
    }

    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: bold;
        transition: all 0.3s;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    /* 状态提示样式 */
    .status-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    .status-success {
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        color: #065F46;
    }

    .status-warning {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        color: #92400E;
    }

    /* 术语词典样式 */
    .dict-table {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# ==================== 工具函数 ====================

def get_project_root():
    """获取项目根目录"""
    return Path(__file__).parent


def get_skill_md_path():
    """获取 skill.md 文件路径"""
    return get_project_root() / "skill.md"


def get_dict_md_path():
    """获取术语词典文件路径"""
    return get_project_root() / "reference" / "02_组织与术语词典.md"


def read_file(file_path):
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return None


def write_file(file_path, content):
    """写入文件内容"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        st.error(f"写入文件失败: {e}")
        return False


def read_reference_file(file_name: str) -> str:
    """
    读取 reference 文件（支持本地和 GitHub 模式）

    Args:
        file_name: 文件名（如 "01_历史纪要重点总结.md"）

    Returns:
        文件内容
    """
    # 优先尝试从 GitHub 读取
    github_mgr = create_github_manager(st)
    if github_mgr:
        content = github_mgr.get_file(f"reference/{file_name}")
        if content:
            return content

    # 回退到本地读取
    local_path = get_project_root() / "reference" / file_name
    return read_file(local_path) or ""


def write_reference_file(file_name: str, content: str, message: str) -> bool:
    """
    写入 reference 文件（支持本地和 GitHub 模式）

    Args:
        file_name: 文件名（如 "01_历史纪要重点总结.md"）
        content: 文件内容
        message: 提交消息（用于 GitHub）

    Returns:
        是否成功
    """
    # 优先尝试写入 GitHub
    github_mgr = create_github_manager(st)
    if github_mgr:
        if github_mgr.update_reference_file(file_name, content, message):
            return True

    # 回退到本地写入
    local_path = get_project_root() / "reference" / file_name
    return write_file(local_path, content)


def read_docx(file_path):
    """读取 .docx 文件内容"""
    try:
        doc = Document(file_path)
        text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
        return text
    except Exception as e:
        st.error(f"读取 .docx 文件失败: {e}")
        return None


def get_latest_files(directory):
    """获取指定目录下最新的文件"""
    try:
        files = []
        for file_path in directory.glob('*'):
            if file_path.is_file():
                files.append((file_path, file_path.stat().st_mtime))
        files.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in files]
    except Exception as e:
        st.error(f"获取文件列表失败: {e}")
        return []


def parse_terminology_dict(content):
    """解析术语词典内容"""
    terms = []
    lines = content.split('\n')
    current_section = None
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            current_section = line
            continue
        if '|' in line and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3 and parts[0] != '错误/口语称呼':
                terms.append({
                    'section': current_section,
                    'wrong': parts[0],
                    'correct': parts[1],
                    'note': parts[2] if len(parts) > 2 else ''
                })
    return terms


def add_term_to_dict(wrong_term, correct_term, note=''):
    """向术语词典添加新词条"""
    dict_path = get_dict_md_path()
    content = read_file(dict_path)

    # 找到合适的位置插入
    lines = content.split('\n')
    insert_index = -1

    for i, line in enumerate(lines):
        if line.startswith('## 口语化表达纠正'):
            insert_index = i + 7  # 跳过表头
            break

    if insert_index == -1:
        # 如果没找到，就追加到末尾
        insert_index = len(lines)

    # 插入新词条
    new_line = f"| {wrong_term} | {correct_term} | {note} |"
    lines.insert(insert_index, new_line)

    # 写回文件
    write_file(dict_path, '\n'.join(lines))
    return True


def export_to_markdown(content, file_path):
    """导出为 Markdown 文件"""
    return write_file(file_path, content)


def export_to_word(content, file_path):
    """导出为 Word 文档"""
    try:
        doc = Document()
        doc.add_heading('管理层周例会纪要', 0)

        # 简单的 Markdown 转 Word 逻辑
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('# '):
                doc.add_heading(line[2:], 0)
            elif line.startswith('## '):
                doc.add_heading(line[3:], 1)
            elif line.startswith('### '):
                doc.add_heading(line[4:], 2)
            elif line.startswith('|') and line.count('|') >= 3:
                # 表格处理（简化版）
                pass
            elif line.startswith('**') and line.endswith('**'):
                doc.add_paragraph(line, style='Strong')
            elif line.startswith('- ') or line.startswith('* '):
                doc.add_paragraph(line[2:], style='List Bullet')
            else:
                doc.add_paragraph(line)

        doc.save(file_path)
        return True
    except Exception as e:
        st.error(f"导出 Word 失败: {e}")
        return False


# ==================== Streamlit 主程序 ====================

def main():
    # 页面标题
    st.markdown('<div class="main-header">📝 会议纪要生成 Agent</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #6B7280; margin-bottom: 2rem;">智能生成 | 格式规范 | 风格一致</p>', unsafe_allow_html=True)

    # ==================== 左侧边栏 - 大脑控制台 ====================
    with st.sidebar:
        st.markdown("## 🧠 大脑控制台")

        # 当前模式显示
        st.markdown("### 当前模式")

        # 检测 GitHub 模式
        github_mgr = create_github_manager(st)
        if github_mgr:
            st.success(f"✅ GitHub Cloud 模式")
            st.caption(f"仓库: {github_mgr.owner}/{github_mgr.repo}")
        else:
            st.info("📁 本地文件模式")

        st.markdown("---")

        # GLM-4 API 配置
        st.markdown("### 🤖 GLM-4 API")

        # 尝试从 secrets 读取 API Key
        api_key = st.secrets.get("GLM_API_KEY", "")

        if not api_key:
            # 如果 secrets 中没有，从 session state 读取或让用户输入
            if "glm_api_key" not in st.session_state:
                st.session_state.glm_api_key = ""

            api_key = st.text_input(
                "API Key",
                type="password",
                value=st.session_state.glm_api_key,
                key="glm_api_key_input",
                help="智谱 GLM-4 API 密钥"
            )

            if api_key:
                st.session_state.glm_api_key = api_key
        else:
            st.success("✅ API Key 已从 Secrets 加载")

        # 测试连接按钮
        if st.button("🔍 测试 API 连接"):
            if api_key:
                client = GLMClient(api_key)
                if client.test_connection():
                    st.success("✅ API 连接成功！")
                else:
                    st.error("❌ API 连接失败，请检查 API Key")
            else:
                st.warning("⚠️ 请先输入 API Key")

        st.markdown("---")

        # 术语词典快捷添加
        st.markdown("### 📖 术语词典")

        st.markdown("**快捷添加术语**")

        wrong_term = st.text_input("错误/口语称呼", key="wrong_term")
        correct_term = st.text_input("正式称呼", key="correct_term")
        note = st.text_input("备注（可选）", key="note")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("添加到词典", type="primary"):
                if wrong_term and correct_term:
                    # 读取当前词典
                    dict_content = read_reference_file("02_组织与术语词典.md")

                    # 找到合适的位置插入
                    lines = dict_content.split('\n') if dict_content else []
                    insert_index = -1

                    for i, line in enumerate(lines):
                        if line.startswith('## 口语化表达纠正'):
                            insert_index = i + 7
                            break

                    if insert_index == -1:
                        insert_index = len(lines)

                    # 插入新词条
                    new_line = f"| {wrong_term} | {correct_term} | {note} |"
                    lines.insert(insert_index, new_line)

                    # 写回文件
                    new_content = '\n'.join(lines)
                    if write_reference_file("02_组织与术语词典.md", new_content, f"添加术语: {wrong_term} → {correct_term}"):
                        st.success(f"✅ 已添加: {wrong_term} → {correct_term}")
                        st.rerun()
                    else:
                        st.error("添加失败")
                else:
                    st.warning("请填写错误称呼和正式称呼")

        with col2:
            if st.button("刷新词典"):
                st.rerun()

        # 显示当前词典统计
        dict_content = read_reference_file("02_组织与术语词典.md")
        if dict_content:
            lines = dict_content.split('\n')
            terms = [line for line in lines if '|' in line and not line.startswith('|---') and not line.startswith('| 错误')]
            st.caption(f"📊 当前词典共 {len(terms)} 个词条")

        # 查看完整词典
        with st.expander("查看完整术语词典"):
            if dict_content:
                st.markdown(dict_content)
            else:
                st.info("术语词典文件不存在")

        st.markdown("---")

        # Reference 文件管理
        st.markdown("### 📚 Reference 文件")

        ref_files = ["01_历史纪要重点总结.md", "02_组织与术语词典.md"]
        st.caption(f"共 {len(ref_files)} 个 Reference 文件")

        for ref_file in ref_files:
            with st.expander(f"📄 {ref_file}"):
                content = read_reference_file(ref_file)
                if content:
                    st.markdown(content)

        st.markdown("---")

        # 使用说明
        st.markdown("### 💡 使用说明")

        with st.expander("查看使用说明"):
            if github_mgr:
                st.markdown("""
                **GitHub Cloud 模式使用指南**

                1. **资料投喂**
                   - 上传录音转写文件（.docx 或 .txt）
                   - 输入手写重点内容

                2. **生成纪要**
                   - 点击「🚀 一键生成会议纪要」按钮
                   - 系统将自动生成标准化会议纪要

                3. **结果处理**
                   - 在结果区域查看生成的纪要
                   - 支持「一键复制」和「下载」功能

                4. **Reference 更新**
                   - 自动从 GitHub 仓库读取历史纪要和术语词典
                   - 更新后的内容自动保存到 GitHub 仓库

                💡 **提示**: 所有数据自动保存到 GitHub，不会丢失！
                """)
            else:
                st.markdown("""
                1. **资料投喂**
                   - 上传录音转写文件（.docx 或 .txt）
                   - 输入手写重点内容

                2. **生成纪要**
                   - 点击「🚀 一键生成会议纪要」按钮
                   - 系统将自动生成标准化会议纪要

                3. **结果处理**
                   - 在结果区域查看生成的纪要
                   - 支持「一键复制」和「下载」功能

                4. **Skill 进化**
                   - 对结果不满意时，在反馈区输入修改要求
                   - 点击「升级 Agent 大脑」自动更新 skill.md
                """)

    # ==================== 右侧主工作区 ====================

    # 标签页导航
    tab1, tab2, tab3 = st.tabs(["📝 纪要生成", "📊 结果展示", "🧠 Skill 进化"])

    # ==================== 标签页1：纪要生成 ====================
    with tab1:
        st.markdown('<div class="section-title">模块 A：资料投喂</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📁 文件上传区")
            st.caption("支持 .docx 或 .txt 格式的录音转写文件")

            # 文件上传
            uploaded_files = st.file_uploader(
                "拖拽或点击上传文件",
                type=['docx', 'txt'],
                accept_multiple_files=True,
                key="file_upload"
            )

            # 显示已上传文件
            if uploaded_files:
                st.markdown("**已上传文件：**")
                for file in uploaded_files:
                    st.success(f"✅ {file.name} ({file.size / 1024:.1f} KB)")

        with col2:
            st.markdown("#### ✍️ 手写重点输入")
            st.caption("输入本次会议的手写重点及特殊关注点")

            # 手写重点输入
            handwritten_notes = st.text_area(
                "手写重点内容",
                placeholder="请输入手写重点，例如：\n\n会议日期：2026-03-03\n参会人员：冷总、刘雨、Alter等\n冷总身份：发言者A\n\n1. 销售进度：果蔬篮需补货1500套\n2. 冷总重点指示...",
                height=250,
                key="handwritten_notes"
            )

        st.markdown("---")

        # 生成按钮
        st.markdown("#### 🚀 生成会议纪要")
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            generate_button = st.button(
                "🚀 一键生成会议纪要",
                type="primary",
                use_container_width=True
            )

        if generate_button:
            with st.spinner("正在生成会议纪要，请稍候..."):
                # 获取 API Key
                api_key = st.secrets.get("GLM_API_KEY", st.session_state.get("glm_api_key", ""))

                if not api_key:
                    st.error("❌ 未配置 GLM-4 API Key，请在侧边栏输入")
                    st.stop()

                # 优先使用上传的文件，如果没有才读取 inputs/ 目录
                transcript_content = ""
                notes_content = handwritten_notes  # 使用文本框输入的手写重点

                # 优先处理上传的文件
                if uploaded_files:
                    # 从上传的文件中读取
                    for file in uploaded_files:
                        if any(keyword in file.name.lower() for keyword in ['转写', '录音', '转录']):
                            # 这是录音转写文件
                            if file.name.endswith('.docx'):
                                import io
                                doc = Document(io.BytesIO(file.getvalue()))
                                transcript_content = '\n'.join([p.text for p in doc.paragraphs])
                            else:
                                transcript_content = file.getvalue().decode('utf-8')

                            st.success(f"✅ 已读取上传文件: {file.name}")
                            break  # 只取第一个转写文件

                    if not transcript_content:
                        st.warning("⚠️ 未找到录音转写文件，请确保文件名包含'转写'、'录音'或'转录'")
                else:
                    # 没有上传文件，尝试从 inputs/ 目录读取（本地模式）
                    inputs_dir = get_project_root() / "inputs"

                    if inputs_dir.exists():
                        files = list(inputs_dir.glob('*'))

                        # 优先找录音转写文件
                        transcript_files = [f for f in files if any(
                            keyword in f.name.lower()
                            for keyword in ['转写', '录音', '转录']
                        ) and f.suffix in ['.docx', '.txt', '.md']]

                        if transcript_files:
                            # 按修改时间排序，取最新的
                            transcript_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                            latest_transcript = transcript_files[0]

                            if latest_transcript.suffix == '.docx':
                                transcript_content = read_docx(latest_transcript)
                            else:
                                transcript_content = read_file(latest_transcript) or ""

                            st.success(f"✅ 已读取本地文件: {latest_transcript.name}")

                if not transcript_content and not notes_content:
                    st.error("❌ 未找到会议文件")
                    st.info("""
                    请确保：
                    1. **Streamlit Cloud**: 在「📁 文件上传区」上传了录音转写文件
                    2. **本地运行**: 将会议文件放入 inputs/ 目录
                    3. 在「✍️ 手写重点输入」输入了手写重点（可选）
                    """)
                    st.stop()

                # 读取 reference 文件
                reference = {
                    '01_历史纪要重点总结.md': read_reference_file("01_历史纪要重点总结.md"),
                    '02_组织与术语词典.md': read_reference_file("02_组织与术语词典.md"),
                    '03_用户偏好.json': read_reference_file("03_用户偏好.json")
                }

                # 调用 GLM-4 API 生成会议纪要
                client = GLMClient(api_key)

                with st.spinner("正在调用 GLM-4 API 生成会议纪要，这可能需要 1-2 分钟..."):
                    generated_minutes = client.generate_minutes(
                        transcript=transcript_content,
                        notes=notes_content,
                        reference=reference
                    )

                if generated_minutes:
                    st.success("✅ 会议纪要生成成功！")

                    # 保存到 session state
                    st.session_state.generated_content = generated_minutes

                    # 自动保存到 outputs/ 目录
                    outputs_dir = get_project_root() / "outputs"
                    outputs_dir.mkdir(exist_ok=True)

                    filename = f"管理周会纪要_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    filepath = outputs_dir / filename

                    if write_file(filepath, generated_minutes):
                        st.success(f"✅ 已保存到: {filepath}")
                    else:
                        st.warning("⚠️ 保存到文件失败，但可以在页面复制")

                    # 提示用户查看结果
                    st.info("👉 请切换到「📊 结果展示」标签页查看生成的会议纪要")
                else:
                    st.error("❌ 会议纪要生成失败，请检查 API Key 或重试")
                    st.info("可能的原因：\n- API Key 无效\n- API 服务暂时不可用\n- 网络连接问题\n\n请检查 API 配置后重试。")

    # ==================== 标签页2：结果展示 ====================
    with tab2:
        st.markdown('<div class="section-title">模块 B：结果展示</div>', unsafe_allow_html=True)

        # 检查是否有生成的内容
        if st.session_state.get("generated_content"):
            content = st.session_state.generated_content

            # 显示生成的纪要
            st.markdown(content)

            st.markdown("---")

            # 操作按钮
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📋 一键复制", use_container_width=True):
                    import pyperclip
                    try:
                        pyperclip.copy(content)
                        st.success("✅ 已复制到剪贴板")
                    except:
                        st.error("❌ 复制失败，请手动复制")

            with col2:
                if st.button("📥 下载为 Markdown", use_container_width=True):
                    outputs_dir = get_project_root() / "outputs"
                    outputs_dir.mkdir(exist_ok=True)
                    file_name = f"会议纪要_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    file_path = outputs_dir / file_name
                    if export_to_markdown(content, file_path):
                        st.success(f"✅ 已保存到 {file_path}")
                    else:
                        st.error("❌ 保存失败")

            with col3:
                if st.button("📄 下载为 Word", use_container_width=True):
                    outputs_dir = get_project_root() / "outputs"
                    outputs_dir.mkdir(exist_ok=True)
                    file_name = f"会议纪要_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                    file_path = outputs_dir / file_name
                    if export_to_word(content, file_path):
                        st.success(f"✅ 已保存到 {file_path}")
                    else:
                        st.error("❌ 保存失败")

            st.markdown("---")

            # 上传最终版纪要
            st.markdown("#### 📤 上传最终版纪要（可选）")
            st.caption("如果您已人工修改完成最终版本，请上传以便更新 Reference")

            final_version = st.file_uploader(
                "上传最终版会议纪要",
                type=['md', 'docx', 'txt'],
                key="final_version_upload"
            )

            if final_version:
                st.success(f"✅ 已接收最终版: {final_version.name}")

                # 读取文件内容
                content = ""
                if final_version.name.endswith('.md'):
                    content = final_version.getvalue().decode('utf-8')
                elif final_version.name.endswith('.txt'):
                    content = final_version.getvalue().decode('utf-8')
                elif final_version.name.endswith('.docx'):
                    import io
                    from docx import Document
                    doc = Document(io.BytesIO(final_version.getvalue()))
                    content = '\n'.join([p.text for p in doc.paragraphs])

                # 简单分析（提取新术语）
                import jieba
                words = jieba.cut(content)
                word_freq = {}
                for word in words:
                    if len(word) > 1:
                        word_freq[word] = word_freq.get(word, 0) + 1

                # 提取潜在新术语
                potential_terms = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

                # 更新历史纪要总结
                summary_content = read_reference_file("01_历史纪要重点总结.md")
                today = datetime.now().strftime('%Y-%m-%d')
                new_entry = f"""

## {today} 自动更新总结

### 新发现要点
- 自动检测到最终版纪要更新
- 文件: {final_version.name}

### 潜在新术语
{chr(10).join([f"- {term[0]} (出现{term[1]}次)" for term in potential_terms])}

### 更新方式
GitHub Cloud 模式自动更新

---
"""
                updated_summary = new_entry + summary_content if summary_content else new_entry
                write_reference_file("01_历史纪要重点总结.md", updated_summary, f"更新历史纪要总结: {final_version.name}")

                st.info("✅ Reference 文件已更新并保存到 GitHub")

        else:
            st.info("👈 请先在「📝 纪要生成」标签页生成会议纪要")

    # ==================== 标签页3：Skill 进化 ====================
    with tab3:
        st.markdown('<div class="section-title">模块 C：Skill 进化反馈回路</div>', unsafe_allow_html=True)

        st.markdown("### 🔄 智能升级 Agent 大脑")

        st.markdown("""
        对生成的会议纪要不满意？或者想永久改变写作风格？

        在下方输入您的修改要求，系统将自动理解并更新 `skill.md` 文件。
        """)

        st.markdown("---")

        # 反馈输入
        feedback_input = st.text_area(
            "告诉 Claude 怎么改：",
            placeholder="例如：\n• 以后把所有提到财务的地方都加上需要左小美审核\n• 冷总发言前要加「冷总指示」前缀\n• TODO事项要按优先级排序",
            height=150,
            key="feedback_input"
        )

        # 常用修改建议
        st.markdown("#### 💡 常用修改建议（点击快速填入）")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 增加数据表格格式", key="suggestion1"):
                feedback_input = "增加销售数据表格，包含：达成率、毛利率、订单量等关键指标"

        with col2:
            if st.button("👥 优化人员称呼", key="suggestion2"):
                feedback_input = "统一人员称呼格式，首次出现使用全名，后续使用简称"

        with col3:
            if st.button("⏰ 强调时间节点", key="suggestion3"):
                feedback_input = "所有事项都必须明确截止日期，优先级事项标注紧急程度"

        st.markdown("---")

        # 升级按钮
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button("🧠 升级 Agent 大脑", type="primary", use_container_width=True):
                if feedback_input:
                    with st.spinner("正在分析您的反馈并更新 skill.md..."):
                        # 这里应该调用 Claude API 分析反馈并更新 skill.md
                        # 由于没有实际的 API 集成，这里演示逻辑
                        st.success("✅ Agent 大脑已升级！")

                        # 读取当前 skill.md
                        skill_content = read_file(skill_md_path)

                        # 在合适位置插入新规则（演示逻辑）
                        new_rule = f"\n\n## 用户自定义规则（{datetime.now().strftime('%Y-%m-%d')}）\n{feedback_input}\n"
                        updated_content = skill_content + new_rule

                        # 写回文件
                        if write_file(skill_md_path, updated_content):
                            st.success("✅ skill.md 已更新")
                            st.info("👉 下次生成会议纪要时将应用新规则")
                        else:
                            st.error("❌ 更新失败")
                else:
                    st.warning("请先输入修改要求")

        st.markdown("---")

        # 当前 skill.md 预览
        st.markdown("### 📄 当前 skill.md 预览")

        if skill_md_path.exists():
            skill_content = read_file(skill_md_path)
            with st.expander("查看完整 skill.md", expanded=False):
                st.markdown(skill_content)
        else:
            st.warning("skill.md 文件不存在")


# ==================== 程序入口 ====================
if __name__ == "__main__":
    # 初始化 session state
    if "generated_content" not in st.session_state:
        st.session_state.generated_content = None

    main()
