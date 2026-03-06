"""
会议纪要自动更新服务
监控reference/目录，检测到最终版纪要后自动更新reference文件
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import jieba


class ReferenceUpdater:
    """Reference文件更新器"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.reference_dir = self.project_root / "reference"
        self.summary_file = self.reference_dir / "01_历史纪要重点总结.md"
        self.dict_file = self.reference_dir / "02_组织与术语词典.md"
        self.preference_file = self.reference_dir / "03_用户偏好.json"
        self.update_log_dir = self.reference_dir / "update_logs"

        # 确保目录存在
        self.update_log_dir.mkdir(exist_ok=True)

        # 加载用户偏好
        self.user_preferences = self._load_preferences()

        # 加载术语词典
        self.terms_dict = self._load_terms_dict()

    def _load_preferences(self):
        """加载用户偏好"""
        if self.preference_file.exists():
            with open(self.preference_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "style_preferences": {},
            "format_preferences": {},
            "focus_areas": [],
            "modification_patterns": []
        }

    def _save_preferences(self):
        """保存用户偏好"""
        with open(self.preference_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_preferences, f, ensure_ascii=False, indent=2)

    def _load_terms_dict(self):
        """加载术语词典"""
        terms = []
        if self.dict_file.exists():
            content = self.dict_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            for line in lines:
                if '|' in line and not line.startswith('|---') and not line.startswith('| 错误'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 3 and parts[0]:
                        terms.append({
                            'wrong': parts[0],
                            'correct': parts[1],
                            'note': parts[2] if len(parts) > 2 else ''
                        })
        return terms

    def analyze_document(self, file_path):
        """分析文档，提取关键信息"""
        content = file_path.read_text(encoding='utf-8')

        # 使用jieba分词提取关键术语
        words = jieba.cut(content)
        word_freq = {}
        for word in words:
            if len(word) > 1:
                word_freq[word] = word_freq.get(word, 0) + 1

        # 提取高频词作为潜在新术语
        potential_terms = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]

        # 分析文档结构
        sections = self._extract_sections(content)

        return {
            'content': content,
            'potential_terms': potential_terms,
            'sections': sections,
            'file_path': file_path
        }

    def _extract_sections(self, content):
        """提取文档章节"""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []

        for line in lines:
            if line.startswith('#'):
                if current_section:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content)
                    })
                current_section = line.strip('#').strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content)
            })

        return sections

    def update_summary(self, analysis_result):
        """更新历史纪要总结"""
        summary_content = self.summary_file.read_text(encoding='utf-8')

        # 添加新的总结条目
        today = datetime.now().strftime('%Y-%m-%d')
        new_entry = f"""

## {today} 自动更新总结

### 新发现要点
- 自动检测到最终版纪要更新
- 文件: {analysis_result['file_path'].name}
- 章节数量: {len(analysis_result['sections'])}

### 潜在新术语
{chr(10).join([f"- {term[0]} (出现{term[1]}次)" for term in analysis_result['potential_terms'][:10]])}

### 更新方式
自动更新，请人工审核后补充完善

---
"""

        # 插入到文件开头
        updated_content = new_entry + summary_content
        self.summary_file.write_text(updated_content, encoding='utf-8')

    def update_dict(self, analysis_result):
        """更新术语词典"""
        dict_content = self.dict_file.read_text(encoding='utf-8')

        # 提取潜在新术语
        new_terms_section = f"""

## 自动发现的新术语（{datetime.now().strftime('%Y-%m-%d')}）

以下术语由系统自动发现，请人工审核后添加到相应章节：

| 错误/口语称呼 | 正式称呼 | 备注 |
|--------------|----------|------|
{chr(10).join([f"| {term[0]} |  | 需要确认 |" for term in analysis_result['potential_terms'][:5]])}

---
"""

        # 插入到文件末尾
        updated_content = dict_content + new_terms_section
        self.dict_file.write_text(updated_content, encoding='utf-8')

    def update_preferences(self, analysis_result):
        """更新用户偏好"""
        content = analysis_result['content']

        # 学习用户的修改模式（简化版）
        patterns = []

        # 检测格式偏好
        if '表格' in content:
            patterns.append('preference:表格格式')

        if '加粗' in content or '**' in content:
            patterns.append('preference:重点加粗')

        # 更新偏好
        if patterns:
            self.user_preferences['modification_patterns'].extend(patterns)
            # 去重，保留最近50条
            self.user_preferences['modification_patterns'] = list(
                dict.fromkeys(self.user_preferences['modification_patterns'][-50:])
            )
            self._save_preferences()

    def log_update(self, file_path, update_type):
        """记录更新日志"""
        log_file = self.update_log_dir / f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        log_content = f"""# 更新日志

**时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**文件:** {file_path.name}
**类型:** {update_type}

## 更新内容

自动更新完成，请人工审核并完善。

---
"""
        log_file.write_text(log_content, encoding='utf-8')

    def process_new_file(self, file_path):
        """处理新文件"""
        try:
            print(f"[{datetime.now()}] 检测到新文件: {file_path.name}")

            # 只处理.md和.docx文件
            if file_path.suffix not in ['.md', '.docx', '.txt']:
                return

            # 跳过日志文件
            if 'update_log' in str(file_path):
                return

            # 分析文档
            analysis = self.analyze_document(file_path)

            # 更新reference文件
            if file_path.name.startswith('管理周会纪要'):
                self.update_summary(analysis)
                self.update_dict(analysis)
                self.update_preferences(analysis)
                self.log_update(file_path, '完整更新')
                print(f"[{datetime.now()}] Reference文件更新完成")

        except Exception as e:
            print(f"[{datetime.now()}] 处理文件出错: {e}")


class FileWatcher(FileSystemEventHandler):
    """文件监控处理器"""

    def __init__(self, updater):
        self.updater = updater
        self.last_processed = {}
        self.cooldown = 2  # 秒

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # 冷却机制：避免同一文件重复处理
        now = time.time()
        if file_path in self.last_processed:
            if now - self.last_processed[file_path] < self.cooldown:
                return

        self.last_processed[file_path] = now
        self.updater.process_new_file(file_path)

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        self.updater.process_new_file(file_path)


def main():
    """主函数"""
    print("=" * 50)
    print("会议纪要自动更新服务启动")
    print("=" * 50)
    print(f"监控目录: {Path(__file__).parent / 'reference'}")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)

    # 创建更新器
    updater = ReferenceUpdater()

    # 创建监控器
    event_handler = FileWatcher(updater)
    observer = Observer()
    observer.schedule(event_handler, str(updater.reference_dir), recursive=False)

    # 启动监控
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止服务...")
        observer.stop()

    observer.join()
    print("服务已停止")


if __name__ == "__main__":
    main()
