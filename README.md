# OriginiumSeal - 源石封印插件

OriginiumSeal 是一个 AstrBot 插件，用来给头像或图片加上源石封印效果。除了命令触发外，它也可以在群聊中响应拍一拍 bot 的行为，并在 bot 具备管理员权限时进行随机禁言。

当前版本：`1.3.0`

## 功能特点

- 支持命令 `/制作源石封印头像`
- 命令后可直接附带图片，优先处理首张附图
- 命令不附图时，仍按发送者头像生成封印图
- 支持监听群聊拍一拍 bot 事件
- 支持可视化配置冷却时间、触发概率、禁言开关、禁言时长、封印透明度
- 随机禁言仅在 bot 为管理员且目标不是管理员或群主时生效

## 使用方法

### 命令生成

- 直接处理自己的头像：
  `/制作源石封印头像`
- 处理命令中附带的第一张图片：
  `/制作源石封印头像` + 图片

### 拍一拍触发

- 仅支持 `aiocqhttp` / OneBot v11 平台
- 仅在群聊中响应拍一拍 bot
- 默认冷却时间为 3600 秒
- 默认触发概率为 0.5

## 配置项

插件支持在 AstrBot WebUI 中直接配置以下参数：

- `enable_poke_trigger`: 是否启用拍一拍触发
- `poke_cooldown_seconds`: 拍一拍冷却时间
- `poke_trigger_probability`: 拍一拍触发概率
- `enable_mute`: 是否启用随机禁言
- `mute_min_seconds`: 最短禁言时长
- `mute_max_seconds`: 最长禁言时长
- `seal_opacity`: 封印图层透明度

## 安装方法

### 一键安装

1. 在插件市场中搜索 `OriginiumSeal`
2. 点击安装并等待完成

### 手动安装

#### 通过 GitHub 链接安装

1. 复制仓库地址：<https://github.com/FengYing1314/astrbot_plugin_OriginiumSeal>
2. 在 AstrBot 插件市场右下角点击 `+`
3. 选择“从 GitHub 上在线下载”
4. 点击安装按钮，等待完成

#### 通过压缩包安装

1. 点击[下载压缩包](https://codeload.github.com/FengYing1314/astrbot_plugin_OriginiumSeal/zip/refs/heads/master)
2. 在 AstrBot 插件市场右下角点击 `+`
3. 选择“从本机上传下载的 .zip 压缩包”
4. 点击安装按钮，等待完成

## 更新说明

### 1.3.0

- 按 AstrBot 官方文档补齐 `requirements.txt`、`support_platforms` 和配置 schema
- 新增命令附图支持，不用换头像也能直接合成封印图
- 将拍一拍行为改为可配置
- 将临时输出改到系统临时目录，避免污染插件目录
- 增强非 QQ 平台与异常场景下的兼容性

## 支持与致谢

感谢 [ptilroko](https://github.com/ptilroko)，此插件的灵感与主要思路来源于该项目。

如有问题，请提交 issue 到 [插件仓库](https://github.com/FengYing1314/astrbot_plugin_OriginiumSeal)。
