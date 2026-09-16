# 发布到 GitHub

PosterLoom 已经整理成可直接上传的 GitHub 仓库。

## 最简单的方法：网页上传

1. 在 GitHub 创建一个空仓库，例如 `posterloom`。
2. 解压 `posterloom-v1.0.0-github-ready-cn.zip`。
3. 打开解压后的 `PosterLoom/`。
4. 把 **PosterLoom 文件夹内部的全部内容** 上传到仓库根目录。
5. Commit。

> 不要把整个 `PosterLoom/` 再套一层上传，否则 GitHub 首页不会直接显示 README。

## 一键发布：GitHub CLI

macOS / Linux：

```bash
bash publish-github.sh posterloom public
```

Windows PowerShell：

```powershell
.\publish-github.ps1 -RepoName posterloom -Visibility public
```

发布后，把 README 中的 `YOUR_USERNAME` 替换成你的 GitHub 用户名或组织名。

如果以后补 Before / After 示例，请只使用你有权公开的照片。
