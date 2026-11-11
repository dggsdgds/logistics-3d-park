# 物流园区 · Three.js 3D Demo

一个极简的 3D 物流园区场景，使用 Three.js（CDN 引入，无需构建工具）实现。

![预览](preview.png)

## 场景内容

- 深灰色网格地面 + 渐变夜空
- 场景中央的大型立方体仓库：波纹金属墙面、装卸月台、卷帘门、屋顶设备、发光招牌
- 仓库旁的公路与来回行驶的货车（带车轮滚动、转向、车灯）
- 暖色太阳光 + 柔和阴影（PCFSoft Shadow Map）
- OrbitControls：鼠标拖拽旋转视角，滚轮缩放

## 运行

```bash
node server.mjs
```

然后打开 http://127.0.0.1:5178

> 也可以直接用任意静态文件服务器托管本目录；Three.js 通过 jsDelivr CDN 加载，需要联网。

## 文件

- `index.html` — 完整场景（HTML + CSS + Three.js 模块）
- `server.mjs` — 零依赖本地静态服务器
