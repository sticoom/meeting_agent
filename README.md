# 会议纪要生成 Agent

基于 GLM-4 的人工智能会议纪要生成系统，支持本地和 Streamlit Cloud 部署。

## ✨ 核心特性

- 🤖 **AI 智能生成**：使用智谱 GLM-4 模型自动生成会议纪要
- 📁 **自动文件读取**：智能识别 inputs/ 目录中的最新会议文件
- 📚 **Reference 管理**：支持历史纪要总结和术语词典，自动学习优化
- 🔄 **GitHub 集成**：支持 Streamlit Cloud 部署，数据持久化到 GitHub
- 🎯 **智能文件定位**：自动识别录音转写和手写重点文件
- ⚠️ **存疑高亮机制**：对模糊信息使用占位符，绝对禁止幻觉
- 📋 **TODO 事项管理**：自动生成 TODO 表格，包含主要事项、负责人、截止日期
- ❄️ **冷总发言优先处理**：完整保留冷总发言，去口语化，保持逻辑顺序
- 🖥️ **Streamlit 界面**：页面简洁美观，支持在线导入导出
- 🌐 **云端支持**：支持 Streamlit Cloud 部署，随时随地访问

---

## 🚀 快速开始

### 本地使用

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
# 复制 .streamlit/secrets.toml.example 为 .streamlit/secrets.toml
# 填入您的 GLM-4 API Key

# 3. 准备会议文件
# 将会议文件放入 inputs/ 目录

# 4. 启动应用
启动小程序.bat

# 或
streamlit run app.py
```

### Streamlit Cloud 部署

1. 推送代码到 GitHub 仓库
2. 在 Streamlit Cloud 配置 Secrets（详见 GitHub部署说明.md）
3. 部署应用

---

## 📁 文件结构

```
Meeting_Agent/
├── app.py                        # Streamlit 主程序
├── skill.md                      # Agent 核心大脑
├── glm_client.py                 # GLM-4 API 客户端
├── github_manager.py              # GitHub 管理模块
├── auto_update.py                # 自动更新服务
├── requirements.txt              # Python 依赖
├── 启动小程序.bat                # Windows 启动脚本
├── .streamlit/
│   ├── secrets.toml             # API 配置（需手动创建）
│   └── secrets.toml.example     # 配置模板
├── reference/                   # 记忆库
│   ├── 01_历史纪要重点总结.md     # 历史纪要要点总结
│   ├── 02_组织与术语词典.md       # 组织架构和术语对照
│   ├── 03_用户偏好.json         # 用户偏好数据
│   └── update_logs/             # 更新日志
├── inputs/                      # 输入文件夹
│   └── [您的会议文件]
├── outputs/                     # 输出文件夹
│   └── [生成的会议纪要]
├── 本地使用说明.md              # 本地使用指南
└── GitHub部署说明.md             # Cloud 部署指南
```

---

## 🎯 核心功能

### 1. 智能文件定位
自动扫描 `inputs/` 目录，识别最新文件：
- 录音转写文件（.docx, .txt）
- 手写重点文件（.txt）
- 按修改时间排序

### 2. AI 智能生成
使用 GLM-4 模型生成会议纪要：
- 应用 skill.md 中的所有规则
- 读取和应用 reference 文件
- 自动去口语化
- 保持冷总发言的逻辑顺序

### 3. Reference 管理
支持历史纪要和术语词典：
- 自动读取 reference 文件
- 应用术语词典纠正错别字
- 学习历史纪要撰写要点

### 4. GitHub 集成
支持 Streamlit Cloud 部署：
- Reference 文件保存在 GitHub
- 自动更新 reference
- 版本控制和协作

### 5. 自动更新
监控 reference/ 目录：
- 检测到新文件自动分析
- 更新历史纪要总结
- 更新术语词典
- 记录更新日志

---

## 📖 使用文档

- 📘 [本地使用说明.md](本地使用说明.md) - 本地环境详细使用指南
- 📗 [GitHub部署说明.md](GitHub部署说明.md) - Streamlit Cloud 部署指南
- 📕 [skill.md](skill.md) - Agent 核心大脑配置
- 📙 [reference/02_组织与术语词典.md](reference/02_组织与术语词典.md) - 术语词典

---

## 🛠️ 依赖安装

```bash
pip install -r requirements.txt
```

**依赖列表：**
- streamlit==1.28.0
- python-docx==1.2.0
- watchdog==3.0.0
- jieba==0.42.1
- requests==2.31.0

---

## 🔧 API 配置

### GLM-4 API
获取地址：https://open.bigmodel.cn/usercenter/apikeys

### GitHub API
获取地址：https://github.com/settings/tokens

---

## 💡 使用技巧

### 本地使用
1. 将会议文件放入 `inputs/`
2. 启动应用：`启动小程序.bat`
3. 点击「🚀 一键生成会议纪要」
4. 在 `outputs/` 查看结果

### Streamlit Cloud
1. 配置 Secrets（GLM_API_KEY, GITHUB_TOKEN 等）
2. 在线上传会议文件
3. 点击生成按钮
4. 下载或复制结果

### Reference 更新
1. 在「📊 结果展示」标签页
2. 上传最终版纪要
3. 系统自动更新 reference
4. 下次生成时应用最新规则

---

## 🐛 常见问题

### Q: API 调用失败？
**A:** 检查：
- GLM_API_KEY 是否正确
- API Key 是否有效
- 网络连接是否正常

### Q: 如何更新 skill.md？
**A:**
- 直接编辑 `skill.md` 文件
- 或在「🧠 Skill 进化」标签页输入修改要求

### Q: 如何添加新术语？
**A:**
- 编辑 `reference/02_组织与术语词典.md`
- 或在侧边栏的「术语词典」快捷添加

### Q: 本地文件和 GitHub 模式有什么区别？
**A:**
- 本地模式：使用本地文件，数据在本地
- GitHub 模式：使用 GitHub 仓库，数据持久化在云端

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                  Streamlit Web 界面                        │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │纪要生成 │  │结果展示 │  │Skill进化 │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │                   │
│       └──────────────┼──────────────┘                   │
│                      ↓                                │
│              ┌──────────────┐                         │
│              │  GLM-4 API   │                         │
│              └──────┬───────┘                         │
│                     ↓                                │
│              ┌──────────────┐                         │
│              │   Reference   │                         │
│              │  文件管理     │                         │
│              └──────┬───────┘                         │
│         ┌──────────┴──────────┐                     │
│         ↓                     ↓                     │
│   本地文件/            GitHub 仓库                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔐 安全建议

1. **不要提交 Secrets**：`.streamlit/secrets.toml` 应在 `.gitignore` 中
2. **定期轮换 Token**：建议每 3-6 个月更换 API Key
3. **权限最小化**：只授予必要的权限
4. **监控使用情况**：定期检查 API 使用情况

---

## 📄 许可证

本项目仅供内部使用。

---

## 📞 技术支持

如有问题或建议，请参考：
- 本地使用说明.md
- GitHub部署说明.md
- skill.md

---

**版本：** V3.0 GLM-4 集成版
**更新时间：** 2026年3月9日
