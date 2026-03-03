# OpenClaw Antigravity Restore Script

[English version](./README_EN.md)

一键恢复并修复 `google-antigravity-auth` 的脚本（适用于 OpenClaw 2026.2.25+）。

> 文件：`restore_antigravity.py`

---

## 中文说明

### 这个脚本会做什么

按顺序执行 4 步：

1. 从 OpenClaw Git 历史拉取 `google-antigravity-auth` 插件源码
2. 对 OpenClaw `dist/*.js` 打兼容补丁（含 antigravity provider 识别、SSRF RFC2544 等）
3. 更新 `~/.openclaw/agents/main/agent/models.json`，添加 `google-antigravity` provider 模型目录
4. 执行 `openclaw plugins enable google-antigravity-auth`

### 运行前要求

- 已安装 OpenClaw（npm 全局安装）
- Python 3.9+
- 能访问 GitHub API（脚本内部用到 `gh api`）
- 建议先备份 OpenClaw 安装目录

### 快速开始

```bash
python restore_antigravity.py
```

完成后按提示执行：

```bash
openclaw gateway restart
openclaw models auth login --provider google-antigravity --set-default
```

### AI / Agent 如何使用这个脚本（给自动化助手）

下面这段可直接给 AI：

```text
任务：在当前机器恢复 OpenClaw 的 google-antigravity-auth。
步骤：
1) 先阅读 restore_antigravity.py，确认将修改哪些目录。
2) 备份 OpenClaw 安装目录（dist 与 extensions）。
3) 运行：python restore_antigravity.py
4) 检查输出是否出现“✅ 修复完成”。
5) 执行：openclaw gateway restart
6) 检查插件状态：openclaw plugins list
7) 若未登录，执行：openclaw models auth login --provider google-antigravity --set-default
8) 回报最终状态（成功/失败 + 失败点）。
```

### 安全模式（建议）

用于生产机的最小风险流程：

1. **先备份**：OpenClaw 安装目录中的 `dist/` 与 `extensions/`
2. **隔离验证**：优先在测试机 / VM 先跑一遍
3. **核对变更**：运行后检查输出是否命中预期补丁
4. **再重启网关**：`openclaw gateway restart`
5. **功能回归**：`openclaw plugins list` + 一次实际登录/调用验证

> 说明：当前脚本没有内置 `--dry-run`，安全模式主要依赖“先备份 + 先测试 + 再上线”。

### 注意事项

- 这是“补丁型”脚本：OpenClaw 升级后可能需要重新运行。
- 脚本会修改已安装包内的 `dist` 文件，请确保你了解风险。
- 建议在测试环境先验证，再用于生产环境。

---

## English Quick Summary

This script restores and patches `google-antigravity-auth` for OpenClaw (2026.2.25+).

Run:

```bash
python restore_antigravity.py
```

Then:

```bash
openclaw gateway restart
openclaw models auth login --provider google-antigravity --set-default
```

For full English documentation, see [README_EN.md](./README_EN.md).

## License

MIT
