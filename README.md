# 锦州港 · 集装箱码头 3D Demo

一个用 Three.js + Blender 资产搭建的港口集装箱码头，第一人称漫游，可上车驾驶，港区规模约 4000 个集装箱。

![港区与卡车](preview.png)

驾驶 HUD（完整方向盘 + 数字速度表，车窗透明）：

![驾驶 HUD](preview-cab.png)

## 场景内容

- 约 600 × 400 的深灰色混凝土码头
- **4060 个 40ft 集装箱**（约为上一版的 10 倍）
  - 中央原有 412 个高精度 Blender 集装箱，8 列 × 6 排、2–4 层
  - 两侧扩展区 3648 个低模 LOD 集装箱，27 列 × 17 排、3–5 层，形成更大的港区
  - 中央约 14.4 m 宽主通道，横向通道可穿行
- **3 辆 Blender 轻卡**停在主通道上
  - 靠近时按 **E** 上车，按 **E** 下车
  - 驾驶时 **↑ / ↓** 加速、倒车，**← / →** 转向
  - 驾驶舱为开放式框架，挡风玻璃和侧窗透明，A 柱改为深色细框
  - 驾驶 HUD：深灰仪表台、完整圆形方向盘（会随转向旋转）、实时数字速度表
  - 只有中央黑底操作提示，移除了左下角重复文字
  - **卡车之间使用 OBB 碰撞箱，不能互相穿透**；步行时玩家也会被车身挡住
- 远海新增一艘**缓慢横向航行的集装箱船**（约 1.1 m/s）
- 岸桥、停靠的集装箱船、海水、系缆桩、锦州港大门
- 第一人称 PointerLockControls 环视

## Blender 资产

所有集装箱和卡车均为 Blender 5.2 LTS 原生建模，无外部付费插件：

- `blender/build_container.py` — 高精度 40ft 集装箱
  - 40 道瓦楞侧板、双开门 8 根锁杆、铰链、ISO 角件、通风口
  - 2048² 烘焙底色贴图，`metalness 0.8 / roughness 0.6`
- `blender/build_container_lod.py` — 低模 LOD 集装箱，用于扩展区
- `blender/build_truck.py` — 轻型厢式卡车
  - 开放式驾驶舱框架，挡风玻璃 + 侧窗透明玻璃
  - 深色细 A/B 柱、深灰仪表台，避免遮挡视线
  - 4 个独立车轮节点、后视镜、灯组、货箱
  - 方向盘和速度表由游戏内 HUD 渲染，避免被屏幕裁切

输出：

- `assets/container.glb` — 高精度集装箱
- `assets/container_lod.glb` — 低模集装箱
- `assets/truck.glb` — 卡车（透明车窗）

## 驾驶与交互

- 走近卡车，底部会出现 `按 E 上车`
- 上车后视角进入驾驶室，HUD 右上角切换为 `DRIVING`，底部提示方向键操作
- 按 **E** 下车，回到第一人称并在车侧落地
- 驾驶时鼠标仍可自由环视（视角相对驾驶室）
- 车辆有简单碰撞，不能穿过集装箱、岸桥腿或大门

## 性能

- 4060 个集装箱只使用 **4 个 InstancedMesh / 4 次 draw call**
  - 高精模 2 个（车体 + 五金）
  - LOD 模 2 个（车体 + 五金）
- 阴影贴图仍只烘焙一次；卡车使用随车移动的 blob 阴影，不触发全场景阴影重绘
- 低模 LOD 让 10 倍集装箱数量仍能保持流畅
- 在 RTX 4060 Laptop GPU 的 Edge 硬件加速环境下实测约 **166 rAF/s**，无掉帧

## 运行

```bash
node server.mjs
```

打开 http://127.0.0.1:5178

> Three.js 与 addons 通过 jsDelivr 的 Gcore 镜像加载，需要联网。

## 文件结构

```
index.html
server.mjs
assets/
  container.glb
  container_lod.glb
  truck.glb
blender/
  build_container.py
  build_container_lod.py
  build_truck.py
  container_preview.png
  truck_preview.png
  textures/container_basecolor.png
preview.png
preview-cab.png
```
