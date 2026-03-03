"""
OpenClaw Google Antigravity Auth - 一键修复脚本
================================================
用途：从 OpenClaw Git 历史恢复 google-antigravity-auth 插件并补丁核心代码
适用：OpenClaw 2026.2.25+ (插件被移除后的版本)
运行：python restore_antigravity.py

支持 Windows / macOS / Linux
升级 OpenClaw 后重新运行此脚本即可恢复功能。
"""

import os
import sys
import json
import subprocess
import base64
import platform
import io

# 修复 Windows GBK 输出编码
if platform.system() == "Windows":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ============================================================
# 跨平台路径解析
# ============================================================

def resolve_openclaw_root():
    """找到 openclaw 包的安装路径"""
    # 方法1: 通过 npm root -g 查找
    try:
        result = subprocess.run(
            ["npm", "root", "-g"], capture_output=True, text=True, timeout=10
        )
        npm_global = result.stdout.strip()
        candidate = os.path.join(npm_global, "openclaw")
        if os.path.isdir(candidate):
            return candidate
    except Exception:
        pass

    # 方法2: 常见路径
    system = platform.system()
    home = os.path.expanduser("~")
    candidates = []
    if system == "Windows":
        candidates.append(os.path.join(os.environ.get("APPDATA", ""), "npm", "node_modules", "openclaw"))
    elif system == "Darwin":
        candidates.append(os.path.join(home, ".nvm", "versions", "node"))  # nvm
        candidates.append("/usr/local/lib/node_modules/openclaw")
        candidates.append(os.path.join(home, ".npm-global", "lib", "node_modules", "openclaw"))
    else:
        candidates.append("/usr/lib/node_modules/openclaw")
        candidates.append("/usr/local/lib/node_modules/openclaw")
        candidates.append(os.path.join(home, ".npm-global", "lib", "node_modules", "openclaw"))

    for c in candidates:
        if os.path.isdir(c):
            return c

    # 方法3: nvm (macOS/Linux) - 遍历版本目录
    if system in ("Darwin", "Linux"):
        nvm_dir = os.path.join(home, ".nvm", "versions", "node")
        if os.path.isdir(nvm_dir):
            for version in sorted(os.listdir(nvm_dir), reverse=True):
                c = os.path.join(nvm_dir, version, "lib", "node_modules", "openclaw")
                if os.path.isdir(c):
                    return c

    return None

def resolve_agent_dir():
    """找到 agent 配置目录"""
    home = os.path.expanduser("~")
    return os.path.join(home, ".openclaw", "agents", "main", "agent")

# ============================================================
# 配置 (运行时解析)
# ============================================================

OPENCLAW_ROOT = None  # resolve_openclaw_root() 在 main() 中设置
DIST_DIR = None
EXT_DIR = None
AGENT_DIR = None

# 插件源码 blob SHA (from OpenClaw repo commit a20c773)
PLUGIN_BLOBS = {
    "index.ts": "055cb15e00b6dc348ec63c954c9eadf7d2ac11b6",
    "openclaw.plugin.json": "2ef207f0486374f74195bda2c10137a0cc6298b8",
    "package.json": "21b897008a0fdb6342cd018633b9ea4c881f6d34",
    "README.md": "4e1dee975eaf58ab1b08426ec39a7f45061298af",
}

# models.json 中要添加的模型
ANTIGRAVITY_MODELS = {
    "baseUrl": "https://cloudcode-pa.googleapis.com",
    "models": [
        {
            "id": "claude-opus-4-6-thinking",
            "name": "Claude Opus 4.6 (Thinking)",
            "provider": "google-antigravity",
            "api": "google-antigravity",
            "contextWindow": 128000,
            "reasoning": True,
            "input": ["text", "image"]
        },
        {
            "id": "claude-opus-4-6",
            "name": "Claude Opus 4.6",
            "provider": "google-antigravity",
            "api": "google-antigravity",
            "contextWindow": 128000,
            "input": ["text", "image"]
        },
        {
            "id": "claude-sonnet-4-6",
            "name": "Claude Sonnet 4.6",
            "provider": "google-antigravity",
            "api": "google-antigravity",
            "contextWindow": 128000,
            "input": ["text", "image"]
        },
        {
            "id": "gemini-3-pro-preview",
            "name": "Gemini 3 Pro",
            "provider": "google-antigravity",
            "api": "google-antigravity",
            "contextWindow": 128000,
            "input": ["text", "image"]
        }
    ]
}

# ============================================================
# 核心代码补丁定义
# ============================================================

DIST_PATCHES = [
    # 1. 移除 LEGACY_REMOVED 限制
    (
        'new Set(["google-antigravity-auth"])',
        'new Set([])'
    ),
    # 2. isGoogleModelApi: 识别 google-antigravity
    (
        'return api === "google-gemini-cli" || api === "google-generative-ai";',
        'return api === "google-gemini-cli" || api === "google-generative-ai" || api === "google-antigravity";'
    ),
    # 3. CLI provider 检查
    (
        'normalized === "google-gemini-cli" || normalized === "google-generative-ai"',
        'normalized === "google-gemini-cli" || normalized === "google-generative-ai" || normalized === "google-antigravity"'
    ),
    # 4. Token 解析
    (
        'if (params.provider === "google-gemini-cli") token = parseGoogleToken',
        'if (params.provider === "google-gemini-cli" || params.provider === "google-antigravity") token = parseGoogleToken'
    ),
    # 5. buildOAuthApiKey: JSON token 格式化
    (
        'return provider === "google-gemini-cli" ? JSON.stringify({',
        'return (provider === "google-gemini-cli" || provider === "google-antigravity") ? JSON.stringify({'
    ),
    # 6. SSRF: 允许 RFC2544 198.18.0.0/15 (代理 TUN 模式虚拟网关 IP)
    (
        'WEB_TOOLS_TRUSTED_NETWORK_SSRF_POLICY = { dangerouslyAllowPrivateNetwork: true }',
        'WEB_TOOLS_TRUSTED_NETWORK_SSRF_POLICY = { dangerouslyAllowPrivateNetwork: true, allowRfc2544BenchmarkRange: true }'
    ),
    # 7. ACP Windows spawn: shell: true (Node.js spawn 在 Windows 找不到 .exe)
    # 注意: 这个补丁需要在 acpx 的 cli.js 里打，不在主 dist 里
]


# ============================================================
# 步骤 1: 下载插件源码
# ============================================================

def step_restore_plugin():
    print("\n[1/4] 恢复插件源码...")
    os.makedirs(EXT_DIR, exist_ok=True)

    for filename, sha in PLUGIN_BLOBS.items():
        target = os.path.join(EXT_DIR, filename)
        if os.path.exists(target) and os.path.getsize(target) > 100:
            print(f"  ✓ {filename} 已存在，跳过")
            continue
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/openclaw/openclaw/git/blobs/{sha}"],
                capture_output=True, text=True, timeout=30
            )
            data = json.loads(result.stdout)
            content = base64.b64decode(data["content"])
            with open(target, "wb") as f:
                f.write(content)
            print(f"  ✓ {filename} ({len(content)} bytes)")
        except Exception as e:
            print(f"  ✗ {filename} 下载失败: {e}")
            return False
    return True


# ============================================================
# 步骤 2: 补丁 dist 文件
# ============================================================

def step_patch_dist():
    print("\n[2/4] 补丁核心代码...")
    total = 0
    for root, dirs, files in os.walk(DIST_DIR):
        for fn in files:
            if not fn.endswith(".js"):
                continue
            p = os.path.join(root, fn)
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                c = f.read()
            original = c
            for old, new in DIST_PATCHES:
                c = c.replace(old, new)
            if c != original:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(c)
                total += 1
                print(f"  ✓ {fn}")
    print(f"  共补丁 {total} 个文件")
    return True


# ============================================================
# 步骤 3: 更新 models.json
# ============================================================

def step_update_models():
    print("\n[3/4] 更新模型目录...")
    models_path = os.path.join(AGENT_DIR, "models.json")

    data = {"providers": {}}
    if os.path.exists(models_path):
        try:
            with open(models_path) as f:
                data = json.load(f)
        except Exception:
            pass

    if "providers" not in data:
        data["providers"] = {}

    if "google-antigravity" in data["providers"]:
        print("  ✓ google-antigravity 已在 models.json 中")
    else:
        data["providers"]["google-antigravity"] = ANTIGRAVITY_MODELS
        with open(models_path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print("  ✓ 已添加 google-antigravity 模型目录")
    return True


# ============================================================
# 步骤 4: 启用插件
# ============================================================

def step_enable_plugin():
    print("\n[4/4] 启用插件...")
    try:
        # Windows 下 npm 全局命令是 .cmd 文件，需要 shell=True
        use_shell = platform.system() == "Windows"
        result = subprocess.run(
            ["openclaw", "plugins", "enable", "google-antigravity-auth"],
            capture_output=True, text=True, timeout=15, shell=use_shell
        )
        output = result.stdout + result.stderr
        if "already enabled" in output.lower() or "Enabled" in output:
            print("  ✓ 插件已启用")
        elif "enabled" in output.lower():
            print("  ✓ 插件已启用")
        else:
            print(f"  ✓ {output.strip()}")
    except Exception as e:
        print(f"  ⚠ 启用失败: {e}")
        print("  手动运行: openclaw plugins enable google-antigravity-auth")
    return True


# ============================================================
# 主流程
# ============================================================

def main():
    global OPENCLAW_ROOT, DIST_DIR, EXT_DIR, AGENT_DIR

    print("=" * 56)
    print("  OpenClaw Google Antigravity Auth 一键修复")
    print("=" * 56)

    # 解析路径
    OPENCLAW_ROOT = resolve_openclaw_root()
    if not OPENCLAW_ROOT:
        print("\n✗ 找不到 OpenClaw 安装目录")
        print("  请确认 OpenClaw 已通过 npm 全局安装")
        sys.exit(1)

    DIST_DIR = os.path.join(OPENCLAW_ROOT, "dist")
    EXT_DIR = os.path.join(OPENCLAW_ROOT, "extensions", "google-antigravity-auth")
    AGENT_DIR = resolve_agent_dir()

    print(f"\n  OpenClaw: {OPENCLAW_ROOT}")
    print(f"  Agent:    {AGENT_DIR}")

    if not os.path.isdir(DIST_DIR):
        print(f"\n✗ 找不到 dist 目录: {DIST_DIR}")
        sys.exit(1)

    steps = [
        step_restore_plugin,
        step_patch_dist,
        step_update_models,
        step_enable_plugin,
    ]

    for step in steps:
        if not step():
            print("\n✗ 修复中断，请检查错误信息")
            sys.exit(1)

    print("\n" + "=" * 56)
    print("  ✅ 修复完成！")
    print("=" * 56)
    print()
    print("接下来：")
    print("  1. 重启 gateway:  openclaw gateway restart")
    print("  2. 登录(首次):    openclaw models auth login --provider google-antigravity --set-default")
    print("  3. 切换模型:      /switch google-antigravity/claude-opus-4-6-thinking")
    print()


if __name__ == "__main__":
    main()
