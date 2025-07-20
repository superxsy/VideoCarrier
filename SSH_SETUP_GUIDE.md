# SSH推送配置指南

本文档详细说明如何配置SSH密钥并推送代码到GitHub仓库。

## 📋 前提条件

- 已安装Git for Windows
- 有GitHub账户
- 可以访问Git Bash

## 🔑 SSH密钥生成与配置

### 第1步：生成SSH密钥

在Git Bash中执行以下命令：

```bash
# 生成SSH密钥（替换为您的GitHub邮箱）
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"
```

**操作说明：**
- 提示保存位置时，直接按Enter（使用默认路径 `~/.ssh/id_rsa`）
- 提示输入密码时，可以直接按Enter（不设密码）或设置一个密码
- 再次确认密码时，重复上一步操作

### 第2步：启动SSH代理并添加密钥

```bash
# 启动SSH代理
eval "$(ssh-agent -s)"

# 添加私钥到SSH代理
ssh-add ~/.ssh/id_rsa
```

### 第3步：复制公钥内容

```bash
# 显示公钥内容
cat ~/.ssh/id_rsa.pub
```

**复制输出的完整内容**（从 `ssh-rsa` 开始到邮箱地址结束）

## 🌐 添加SSH密钥到GitHub

1. **登录GitHub**：访问 [github.com](https://github.com)

2. **进入SSH设置**：
   - 点击右上角头像 → Settings
   - 左侧菜单选择 "SSH and GPG keys"

3. **添加新密钥**：
   - 点击 "New SSH key" 按钮
   - Title：填写描述性名称（如 `VideoCarrier-Windows`）
   - Key：粘贴第3步复制的公钥内容
   - 点击 "Add SSH key"

## 🔍 验证SSH连接

```bash
# 测试SSH连接
ssh -T git@github.com
```

**预期输出：**
```
Hi username! You've successfully authenticated, but GitHub does not provide shell access.
```

## 🚀 配置项目并推送代码

### 配置远程仓库

```bash
# 切换到项目目录
cd /path/to/your/project

# 设置SSH远程URL
git remote set-url origin git@github.com:username/repository.git

# 或者添加新的远程仓库
git remote add origin git@github.com:username/repository.git
```

### 推送代码

```bash
# 添加所有文件
git add .

# 提交更改
git commit -m "Your commit message"

# 推送到main分支
git push -u origin main
```

## ⚠️ 常见问题解决

### 1. 首次连接提示

```
The authenticity of host 'github.com' can't be established.
Are you sure you want to continue connecting (yes/no)?
```

**解决方案：** 输入 `yes` 并按Enter

### 2. 权限被拒绝

```
Permission denied (publickey)
```

**解决方案：**
- 确保公钥已正确添加到GitHub
- 检查SSH代理是否运行：`ssh-add -l`
- 重新添加密钥：`ssh-add ~/.ssh/id_rsa`

### 3. 密钥未找到

```
/c/Users/Username/.ssh/id_rsa: No such file or directory
```

**解决方案：** 重新执行第1步生成SSH密钥

### 4. 远程仓库冲突

```
! [rejected] main -> main (fetch first)
```

**解决方案：**
```bash
# 强制推送（谨慎使用）
git push --force origin main

# 或者先拉取再推送
git pull origin main --allow-unrelated-histories
git push origin main
```

## 🔧 Windows PowerShell注意事项

- PowerShell不支持 `&&` 操作符，需要分别执行命令
- 路径格式使用Windows格式：`C:\path\to\directory`
- 建议使用Git Bash执行SSH相关命令

## 📝 最佳实践

1. **定期备份SSH密钥**
2. **为不同项目使用不同的SSH密钥**（可选）
3. **设置密钥密码**以增强安全性
4. **定期更新SSH密钥**
5. **不要将私钥文件提交到版本控制**

## 🔗 相关链接

- [GitHub SSH文档](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [Git官方文档](https://git-scm.com/docs)
- [SSH密钥管理最佳实践](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys)

---

**注意：** 本文档基于VideoCarrier项目的实际配置经验编写，适用于Windows环境下的Git操作。