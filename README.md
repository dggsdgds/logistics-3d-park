# 锦州港 · 集装箱码头 3D Demo

一个完全用 Three.js（CDN 引入）程序化生成的港口集装箱码头场景，支持第一人称漫游。集装箱已从代码方块升级为 **Blender 手工建模 + 烘焙材质** 的 GLB 资产，并通过 `InstancedMesh` 批量渲染。

![码头预览](preview.png)

## 场景内容

- 600 × 400 的深灰色混凝土码头地面，带混凝土板缝与码头岸线
- **412 个 40ft 集装箱**，按真实尺寸 `2.44 × 2.59 × 12.19 m` 生成
  - 左右各 8 列、每列 6 排，堆叠 2–4 层
  - 红、蓝、绿、黄、橙、灰、白等颜色随机分配
  - 中央留出约 **14.4 m 宽的主通道**，另有横向通道可以穿行
- 码头岸桥（STS 龙门吊）及其吊具上的集装箱、停靠的集装箱船、海水、系缆桩
- “锦州港 / JINZHOU PORT” 大门
- 暖色太阳平行光 + PCFSoft 柔化阴影
- 第一人称漫游：点击锁定鼠标、自由环视、WASD 移动

## Blender 集装箱资产

参考 iBlender 集装箱建模/材质视频的题材与标准 40ft 箱结构，在 **Blender 5.2 LTS** 中重新建模：

- 真实 40ft 外尺寸：12.192 × 2.438 × 2.591 m，原点在几何中心
- 几何细节：
  - 两侧 40 道梯形瓦楞钢板 + 前墙/门板瓦楞
  - 8 个 ISO 角件、上下横梁、角柱
  - 双开门 + 8 根锁杆、锁杆导座、门把手、铰链、门缝压条
  - 侧面通风口
- 材质：`MeshStandardMaterial`（导出为 glTF PBR），`metalness = 0.8`、`roughness = 0.6`
- UV 展开后，在 Cycles 中烘焙了一张 **2048² 的底色调**（中性底漆 + 底部污渍/锈迹），因此每个实例可以用 `instanceColor` 独立染色
- 五金件使用独立的深色金属材质

Blender 源文件：

- `blender/build_container.py` — 完整建模、UV、材质、烘焙、预览渲染、GLB 导出脚本
- `blender/container_preview.png` — Blender 预览
- `blender/textures/container_basecolor.png` — 烘焙出的底色贴图
- `assets/container.glb` — 最终资产（约 1.8 MB，贴图内嵌）

## 技术实现

- 浏览器用 `GLTFLoader` 加载 `assets/container.glb`
- 按材质拆成 **painted body** 和 **hardware** 两组 `InstancedMesh`，412 个实例各共享同一份几何体
- 集装箱总面数约 11.7k 三角面/个，412 个实例共约 480 万三角面，全部由 GPU 实例化渲染
- `instanceColor` 仅作用于车身，五金件保持深色金属
- 阴影贴图仍只烘焙一次（4096²），水面只做纹理偏移
- `RoomEnvironment` + `PMREMGenerator` 提供环境反射，`AmbientLight` 让暗部过渡更自然
- 如果 GLB 加载失败，会自动回退到原来的低模箱子，不会白屏

## 性能

- 集装箱主体+五金件共 **2 个 InstancedMesh / 2 次 draw call**
- 静态阴影贴图只在启动时生成一次
- 环境贴图只在启动时 PMREM 预计算一次
- 在 RTX 4060 Laptop GPU 上实测流畅（Chrome/Edge 硬件 GPU，无掉帧）

## 操作

打开页面后点击画面进入码头：鼠标锁定并隐藏，移动鼠标环视，W/A/S/D 移动，ESC 释放鼠标。

## 运行

```bash
node server.mjs
```

然后打开 http://127.0.0.1:5178

> Three.js 和 addons 通过 jsDelivr 的 Gcore 镜像加载，需要联网。
