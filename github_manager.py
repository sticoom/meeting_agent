"""
GitHub 管理模块
处理 GitHub API 操作，用于 Streamlit Cloud 环境下的 reference 文件读写
"""

import base64
import requests
from pathlib import Path
from typing import Optional, Dict, Any


class GitHubManager:
    """GitHub 管理器"""

    def __init__(self, token: str, owner: str, repo: str):
        """
        初始化 GitHub 管理器

        Args:
            token: GitHub 个人访问令牌
            owner: 仓库所有者用户名
            repo: 仓库名称
        """
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_file(self, path: str) -> Optional[str]:
        """
        获取 GitHub 仓库中的文件内容

        Args:
            path: 文件路径（相对于仓库根目录）

        Returns:
            文件内容，如果文件不存在返回 None
        """
        url = f"{self.base_url}/contents/{path}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()

            # 解码 base64 内容
            content = data.get('content', '')
            if content:
                decoded = base64.b64decode(content).decode('utf-8')
                print(f"✅ GitHub 读取成功: {path} ({len(decoded)} 字符)")
                return decoded

            print(f"⚠️ GitHub 文件存在但内容为空: {path}")
            return None

        except requests.exceptions.Timeout:
            print(f"⏱️ GitHub API 超时 [{path}]")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"❌ GitHub HTTP 错误 [{path}]: {e}")
            print(f"   HTTP 状态码: {e.response.status_code if e.response else '未知'}")
            return None
        except Exception as e:
            print(f"❌ GitHub API 调用失败 [{path}]: {type(e).__name__}")
            print(f"   错误详情: {e}")
            return None

    def update_file(self, path: str, content: str, message: str) -> bool:
        """
        更新 GitHub 仓库中的文件

        Args:
            path: 文件路径（相对于仓库根目录）
            content: 新的文件内容
            message: 提交消息

        Returns:
            是否成功
        """
        url = f"{self.base_url}/contents/{path}"

        try:
            # 获取当前文件的 SHA
            response = requests.get(url, headers=self.headers)
            sha = None

            if response.status_code == 200:
                sha = response.json().get('sha')
            elif response.status_code != 404:
                response.raise_for_status()

            # 更新或创建文件
            data = {
                "message": message,
                "content": base64.b64encode(content.encode()).decode()
            }

            if sha:
                data["sha"] = sha  # 更新现有文件
            else:
                # 创建新文件，确保目录结构
                parent_path = str(Path(path).parent)
                if parent_path != '.':
                    self._ensure_directory(parent_path)

            response = requests.put(url, json=data, headers=self.headers)
            response.raise_for_status()

            return True

        except Exception as e:
            print(f"更新文件失败 [{path}]: {e}")
            return False

    def _ensure_directory(self, dir_path: str) -> bool:
        """确保目录存在（通过创建 .gitkeep 文件）"""
        try:
            gitkeep_path = f"{dir_path}/.gitkeep"
            if not self.get_file(gitkeep_path):
                self.update_file(gitkeep_path, "", f"Create directory {dir_path}")
            return True
        except Exception as e:
            print(f"创建目录失败 [{dir_path}]: {e}")
            return False

    def list_files(self, path: str = "") -> list:
        """
        列出指定路径下的文件

        Args:
            path: 目录路径（相对于仓库根目录）

        Returns:
            文件列表
        """
        url = f"{self.base_url}/contents/{path}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            return [item['name'] for item in data if item['type'] == 'file']

        except Exception as e:
            print(f"列出文件失败 [{path}]: {e}")
            return []

    def get_reference_files(self) -> Dict[str, str]:
        """
        获取所有 reference 文件内容

        Returns:
            {文件名: 文件内容}
        """
        print("📖 开始获取 reference 文件...")
        files = {}
        reference_files = [
            "reference/01_历史纪要重点总结.md",
            "reference/02_组织与术语词典.md",
            "reference/03_用户偏好.json",
            "reference/03_风格学习记录.md",
            "reference/04_风格模板.md"
        ]

        for file_path in reference_files:
            print(f"   正在读取: {file_path}")
            content = self.get_file(file_path)
            if content:
                files[file_path] = content
                print(f"   ✅ 读取成功: {file_path} ({len(content)} 字符)")
            else:
                print(f"   ❌ 读取失败: {file_path}")

        print(f"📊 Reference 文件统计: {len(files)} 个成功, {len(reference_files) - len(files)} 个失败")
        return files

    def update_reference_file(self, file_name: str, content: str, message: str) -> bool:
        """
        更新 reference 目录下的文件

        Args:
            file_name: 文件名（如 "01_历史纪要重点总结.md"）
            content: 新的文件内容
            message: 提交消息

        Returns:
            是否成功
        """
        path = f"reference/{file_name}"
        return self.update_file(path, content, message)

    def create_update_log(self, log_content: str) -> bool:
        """
        创建更新日志

        Args:
            log_content: 日志内容

        Returns:
            是否成功
        """
        from datetime import datetime

        log_filename = f"update_logs/update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        return self.update_file(
            log_filename,
            log_content,
            f"Create update log: {log_filename}"
        )


def create_github_manager(st) -> Optional[GitHubManager]:
    """
    从 Streamlit session state 创建 GitHub 管理器

    Args:
        st: Streamlit 对象

    Returns:
        GitHub 管理器实例，如果配置不完整返回 None
    """
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        owner = st.secrets.get("GITHUB_OWNER")
        repo = st.secrets.get("GITHUB_REPO")

        # 验证配置完整性
        if not all([token, owner, repo]):
            print("⚠️ GitHub 配置不完整:")
            if not token:
                print("   - GITHUB_TOKEN: 未设置")
            if not owner:
                print("   - GITHUB_OWNER: 未设置")
            if not repo:
                print("   - GITHUB_REPO: 未设置")
            return None

        # 验证 token 格式
        if token and not token.startswith(('github_pat_', 'ghp_', 'gho_', 'ghu_')):
            print(f"⚠️ GitHub Token 格式可能不正确: {token[:10]}...")
            print("   Token 应该以 'github_pat_' 或 'ghp_' 开头")

        print(f"✅ GitHub 配置验证通过: {owner}/{repo}")

        return GitHubManager(token, owner, repo)

    except Exception as e:
        print(f"❌ GitHub 管理器初始化失败: {e}")
        return None


def is_github_mode(st) -> bool:
    """
    检测是否在 GitHub 模式下运行

    Args:
        st: Streamlit 对象

    Returns:
        是否启用 GitHub 模式
    """
    manager = create_github_manager(st)
    return manager is not None
