# PosterLoom 安装说明

## 从 GitHub 安装到 Codex

仓库发布后：

```text
$skill-installer install https://github.com/YOUR_USERNAME/posterloom/tree/main/posterloom
```

把 `YOUR_USERNAME` 替换成你的 GitHub 用户名或组织名。

## 本地一键安装

```bash
python install.py
```

指定目录：

```bash
python install.py --target ~/.agents/skills
python install.py --target ~/.codex/skills
```

覆盖已有安装：

```bash
python install.py --force
```

如果没有指定 `--target`，安装器会自动寻找常见的 Agent Skills 目录，并把仓库中的 `posterloom/` 安装进去。

安装完成后，如果宿主没有自动发现新 Skill，请重新加载或重启宿主。
