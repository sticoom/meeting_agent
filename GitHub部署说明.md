# GitHub + Streamlit Cloud 部署说明

## 部署流程

### 1. 准备 GitHub 仓库

确保您的 GitHub 仓库包含以下文件：

```
your-repo/
├── app.py
├── skill.md
├── requirements.txt
├── github_manager.py
├── glm_client.py
├── .streamlit/
│   └── secrets.toml
├── reference/
│   ├── 01_历史纪要重点总结.md
│   ├── 02_组织与术语词典.md
│   └── 03_用户偏好.json
├── inputs/
│   ├── 会议录音转写.docx
│   └── 手写重点.txt
└── outputs/
    └── 管理周会纪要_*.md
```

### 2. 获取 API Keys

#### 2.1 GitHub Personal Access Token
1. 访问 https://github.com/settings/tokens
2. 点击 **Generate new token (classic)**
3. 设置名称（如：Meeting Agent Token）
4. 勾选权限：
   - ✅ `repo` (完整的仓库访问权限)
5. 点击生成并复制 token（只显示一次，请妥善保存）

#### 2.2 GLM-4 API Key
1. 访问 https://open.bigmodel.cn/usercenter/apikeys
2. 点击 **创建新的 API Key**
3. 设置名称（如：Meeting Agent）
4. 复制 API Key

### 3. 配置 Streamlit Secrets

在您的 GitHub 仓库中配置 Streamlit Secrets：

**方式一：通过 Streamlit Cloud UI 配置（推荐）**
1. 登录 https://share.streamlit.io
2. 选择您的应用 → Settings → Secrets
3. 添加以下四个环境变量：
   ```
   GITHUB_TOKEN = "your_github_personal_access_token_here"
   GITHUB_OWNER = "your_username_here"
   GITHUB_REPO = "your_repository_name_here"
   GLM_API_KEY = "your_glm_api_key_here"
   ```

**方式二：通过 .streamlit/secrets.toml（仅用于本地测试）**
1. 复制 `.streamlit/secrets.toml.example` 为 `.streamlit/secrets.toml`
2. 填入实际值：
   ```toml
   GITHUB_TOKEN = "your_github_personal_access_token_here"
   GITHUB_OWNER = "your_username_here"
   GITHUB_REPO = "your_repository_name_here"
   ```
3. ⚠️ **注意**：`secrets.toml` 文件不应提交到 GitHub

### 4. 部署到 Streamlit Cloud

**方式一：通过 GitHub 集成（推荐）**
1. 登录 https://share.streamlit.io
2. 点击 **New app**
3. 选择您的 GitHub 仓库
4. 选择分支（通常是 main 或 master）
5. 设置主文件路径：`app.py`
6. 点击 **Deploy**

**方式二：通过命令行**
```bash
pip install streamlit
streamlit deploy
```

### 5. 初始化 Reference 文件

首次部署后，需要在 GitHub 仓库中创建初始的 reference 文件：

1. 在 GitHub 仓库中创建 `reference/` 目录
2. 添加以下文件：
   - `01_历史纪要重点总结.md` - 初始模板或留空
   - `02_组织与术语词典.md` - 初始模板或留空
   - `03_用户偏好.json` - 初始配置（见本项目的 reference/03_用户偏好.json）

或者，您可以在应用中通过 GitHub API 自动创建这些文件（需要修改代码支持）。

---

## 使用说明

### 本地使用

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 .streamlit/secrets.toml（本地测试用）
# 复制 .streamlit/secrets.toml.example 并填入实际值

# 启动
streamlit run app.py
```

### Streamlit Cloud 使用

1. 确保在 Streamlit Cloud 的 Secrets 中配置了 GitHub 凭证
2. 访问您的应用 URL（如：https://your-app.streamlit.app）
3. 应用会自动检测 GitHub 模式并从 GitHub 读取 reference 文件

---

## 功能特性

### ✅ GitHub 模式下的功能

- **自动读取 reference**：从 GitHub 仓库读取历史纪要和术语词典
- **自动保存更新**：更新后的内容自动提交到 GitHub
- **数据持久化**：所有数据保存在 GitHub，不会丢失
- **版本控制**：自动记录每次更新历史
- **协作友好**：团队成员可以查看和修改 reference 文件

### ⚠️ 注意事项

1. **权限要求**：GitHub Token 需要 `repo` 权限才能读写文件
2. **API 限制**：GitHub API 有速率限制，频繁更新可能触发限制
3. **文件大小**：GitHub 单文件限制为 100MB，一般够用
4. **安全提示**：不要在代码中硬编码 GitHub Token，始终使用 Secrets

---

## 故障排查

### 问题：应用显示"本地文件模式"

**原因**：未正确配置 GitHub 凭证

**解决方法**：
1. 检查 Streamlit Cloud 的 Secrets 是否正确配置
2. 确保 `GITHUB_TOKEN`、`GITHUB_OWNER`、`GITHUB_REPO` 三个值都已设置
3. 检查 GitHub Token 是否有足够的权限（需要 `repo` 权限）

### 问题：无法读取 reference 文件

**原因**：GitHub 仓库中不存在 reference 文件

**解决方法**：
1. 在 GitHub 仓库中创建 `reference/` 目录
2. 添加所需的 reference 文件
3. 重新部署应用或刷新页面

### 问题：更新失败

**原因**：GitHub API 请求失败

**解决方法**：
1. 检查网络连接
2. 验证 GitHub Token 是否有效
3. 检查 Token 权限是否包含 `repo`
4. 查看浏览器控制台的错误信息

---

## 进阶配置

### 使用多个 GitHub 仓库

如果需要在不同的环境中使用不同的仓库，可以通过修改 `secrets.toml` 或 Streamlit Secrets 切换：

```toml
# 开发环境
GITHUB_TOKEN = "dev_token"
GITHUB_OWNER = "your_username"
GITHUB_REPO = "meeting-agent-dev"

# 生产环境
GITHUB_TOKEN = "prod_token"
GITHUB_OWNER = "your_username"
GITHUB_REPO = "meeting-agent-prod"
```

### 自定义更新消息

在 `github_manager.py` 中修改 `update_reference_file` 方法，可以自定义提交消息格式：

```python
message = f"[Auto] Update {file_name} at {datetime.now()}"
```

---

## 安全建议

1. **Token 权限最小化**：只授予必要的权限（`repo` 已足够）
2. **定期轮换 Token**：建议每 3-6 个月更换一次 GitHub Token
3. **监控使用情况**：在 GitHub Settings → Developer settings → Personal access tokens 中监控 token 使用情况
4. **不要提交 Secrets**：`.streamlit/secrets.toml` 应在 `.gitignore` 中

---

## 技术支持

如遇到问题，请检查：
1. GitHub Token 是否有效且有足够权限
2. Streamlit Secrets 是否正确配置
3. 仓库路径是否正确
4. 应用日志中的错误信息

---

**最后更新时间：** 2026年3月6日
**版本：** V1.0
