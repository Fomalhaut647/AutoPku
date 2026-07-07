---
name: autopku-tool-pku3b-setup
description: PKU教学网工具 pku3b 的安装、配置和登录
---

# pku3b 工具配置

## 安装检查

```bash
which pku3b 2>/dev/null || echo "NOT_FOUND"
```

## 安装

### macOS Apple Silicon
```bash
cd /tmp
curl -LO "https://github.com/sshwy/pku3b/releases/download/0.11.0/pku3b-0.11.0-aarch64-apple-darwin.tar.gz"
tar -xzf pku3b-0.11.0-aarch64-apple-darwin.tar.gz
chmod +x pku3b-0.11.0-aarch64-apple-darwin/pku3b
ln -sf pku3b-0.11.0-aarch64-apple-darwin/pku3b pku3b
./pku3b --version
```

### 其他平台
从 [sshwy/pku3b releases](https://github.com/sshwy/pku3b/releases) 下载对应版本。

> **版本说明**: v0.11.0+ 支持公告 (`ann`) 和课表 (`ct`) 功能

## 登录

`pku3b init` 只需执行一次，凭证持久化到 `~/Library/Application Support/org.sshwy.pku3b/cfg.toml`。

### 1. 检查是否已登录

```bash
/tmp/pku3b a ls 2>&1 || echo "NOT_LOGGED_IN"
```

正常返回作业列表 → 已登录，跳过步骤 2-3。返回 `NOT_LOGGED_IN` → 执行步骤 2。

### 2. TTY-safe 登录（仅在未登录时）

```bash
cat > /tmp/pku3b_login.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 30
spawn /tmp/pku3b init
expect "username:"
send "学号\r"
expect "password:"
send "密码\r"
expect eof
EOF
chmod +x /tmp/pku3b_login.exp
/tmp/pku3b_login.exp
```

`pku3b init` 检查 TTY，直接管道输入会报错 "input device is not a TTY"，必须使用 expect。

### 3. 验证并清理

```bash
# 验证登录成功
/tmp/pku3b a ls

# 立即覆写临时文件，清除明文密码
echo "" > /tmp/pku3b_login.exp
```

## 常用命令

```bash
# 作业
/tmp/pku3b a ls --all-term          # 所有学期作业
/tmp/pku3b a -f ls -a               # 强制刷新缓存列所有作业（含已完成）
/tmp/pku3b a download <ID> -d <dir> # 下载附件
/tmp/pku3b a submit <ID> <file>     # 提交作业（一次只接受单个文件）

# 公告
/tmp/pku3b ann ls                   # 列出公告
/tmp/pku3b ann show <ID>            # 查看公告详情

# 课表
/tmp/pku3b ct -r                    # 获取课表 JSON

# 选课
/tmp/pku3b s -d major show          # 主修课程
```

## 踩坑记录

- `pku3b init` 需要交互式输入，直接管道输入不工作
- `pku3b auth status/login` 命令不存在，正确命令是 `pku3b init`
- `pku3b s -d major show` 可能在某些账号返回 `302 Found`，作为可选步骤处理
- **pku3b 有本地缓存**：提交作业后直接 `a ls` 看不到状态更新，必须 `a -f ls -a` 强制刷新才能确认提交成功
- **`a submit` 一次只接受单个文件**：多文件（PDF + 多份源码）需先 `zip` 打包成一个压缩包再提交
- 作业 ID 是 16 位 hex，从 `a ls` 输出末尾的灰色字段提取（解析时注意剥离 ANSI 颜色码，见 `data-parser.md`）
