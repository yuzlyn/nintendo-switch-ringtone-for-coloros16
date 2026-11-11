# Nintendo Switch 音效 · ColorOS 16 / 17

把系统的 UI 音效和通知音换成 Nintendo Switch 的原声采样。

**已在 ColorOS 16 与 ColorOS 17（Android 17，一加 13）上实机验证**；C17 把 UI 音效目录搬到了 `/my_product/media/audio/ui`，模块会自动探测并继续生效。

**只替换素材包里真实存在的原始音效**，不做任何合成、拼接或改编。游戏机上没有的声音（铃声、闹钟、天气提醒、开关机音），一律保持手机原样。

- 适用系统：ColorOS 16 / 17（Android 16 / 17）
- 实测机型：一加 13（ColorOS 16 / 17）
- 权限要求：KernelSU / Magisk / APatch 任一
- 音效库：212 个可选音效（204 个固件采样 + 8 个合成音）
- 替换槽位：139 个，可逐个开关

## 特性

内置 WebUI，不用改配置、不用重刷模块：

- **逐个槽位开关**：139 个槽位每个都有独立开关，关掉就保持手机原声
- **自由指定音效**：任意槽位都可以从 212 个音效里挑，不再是一对一写死
- **点行试听 / 点「使用」保存**：试听和保存是两个动作，误触不会改掉已选音效
- **恢复默认**：一键回到出厂映射
- 改动保存后重启生效，界面会提示

## 替换范围

ColorOS 17 把 UI 音效从 `my_stock` 搬到了 `my_product`，所以每组音效都按候选目录依次探测，**所有实际存在的目录都会被挂载**，不存在的自动跳过并写入日志。

| 音效组 | 槽位 | 内容 | 目标目录（按顺序探测） |
| --- | --- | --- | --- |
| 按键 / UI | 22 | 按键、锁屏/解锁、截图、相机、低电量、Dock、充电 | `/my_product/media/audio/ui`、`/product/media/audio/ui` |
| 触摸 / 系统 | 42 | 触摸反馈、删除、错误、音量条、滚轮、电池提示、电子书翻页 | `/my_product/media/audio/ui`、`/my_stock/media/audio/ui`、`/system/media/audio/ui` |
| 通知音 | 75 | 通知音 | `/data/oplus/multimedia/notifications`、`/data/oplus/media/notifications`、`/my_product/media/audio/notifications` |

**不替换**：铃声、天气提醒、闹钟、`poweron` / `poweroff`、倒计时音、`/data/oplus/multimedia/ui` 整个目录。这些在游戏机上没有对应行为，保持手机原声。

ColorOS 17 的通知音目录比 16 少了一批文件，实测 139 个槽位命中 110 个，其余 29 个自动跳过（对应文件在新系统上不存在），WebUI 会把它们标成「此機型沒有這個音效檔案」。

## 映射逻辑

默认映射按 Switch 上的**实际行为**对应，而不是随便挑音效：

| 手机事件 | Switch 上的对应行为 | 使用音效 |
| --- | --- | --- |
| 按键点击 | 唤醒画面按 A 键 | `SeUnlock` |
| 回车 / 确认 | 唤醒画面按 ZL | `SeUnlockKeyZL` |
| 空格 / 删除 | 唤醒画面按 + / - | `SeUnlockPlus` / `SeUnlockMinus` |
| 锁屏 | 进入睡眠模式 | `StartupSleep` |
| 解锁 | 唤醒按键 | `SeUnlock` |
| 列表焦点移动 | HOME 光标移动 | `SeSelectFocus` |
| 操作无效 | 无效输入 | `SeKeyErrorTouch` |
| 截图 | 截图保存提示 | `SeCheckBtnPressFinish` |
| 相机快门 / 对焦 | 相册看图 | `SeCheckBtnPressFinish` / `SeVgc_Dialog_Check` |
| 低电量 | 电量不足提示 | `SeWarning_Dtt` |
| 摘除底座 | 卡带弹出 | `SeVgcCard_Eject` |
| 通知 | 好友上线 / 新闻推送 / 下载完成 | 75 个原始通知音 |

音量条、滚轮使用 `SeVgcCard_Move`（光标移动音）。以上都只是默认值，都可以在 WebUI 里改。

## 充电音

充电音是唯一一处例外：用 Joy-Con 滑轨吸附的听感**手工合成**（机械轻响 + 两声上行），因为素材包里没有对应的插入充电提示音。不想用合成音就在 WebUI 里把 `Usb.ogg`、`charge.mp3`、`charging.ogg`、`Dock.ogg` 这四项关掉。

## 安装

1. 下载 Release 里的 `NS-Ringtone-v2.0.1.zip`（不要解压）
2. 模块管理器 → 从本地安装 → 选中该 zip
3. 重启
4. 重启后在模块页面点 **WebUI** 调整音效

覆盖安装会保留已有的音效选择（`data/sounds.conf` 会被迁移）。开机后可在 `/data/adb/ns-ringtone.log` 查看每个槽位的挂载结果。

> 如果设备装了 metamodule（`/data/adb/metamodule`），KernelSU Next 会拦截命令行的 `ksud module install`，报 `Metamodule installation blocked`。这不是安装包的问题，从模块管理器界面安装即可。

## 使用 WebUI

- 顶部卡片显示「已替换 / 保持原声 / 音效库数量」，以及当前系统上不存在的槽位数量
- 列表按三组展开，每行右侧开关控制是否替换
- 点一行打开音效选择面板：
  - **点一行 = 试听**（左侧圆形按钮也是试听）
  - **点右侧「使用」= 保存**，保存后该槽位立即变成新音效
  - 「当前」表示该槽位正在用的音效
- 右上角「恢复默认」把所有槽位还原成出厂映射

## 卸载

模块管理器里删除 `ns-ringtone` 后重启。挂载是每个开机周期重建的，重启即消失；系统分区的原始文件从未被修改，铃声 / 闹钟设置也不会被改动。

> 从 v1.0 升级：v1.0 会改写当前铃声和闹钟设置，v1.1 起不再改动。升级后请自行在「设置 → 声音与振动」里重选铃声和闹钟。

## 已知限制

- 第三方 App 自带的提示音（微信、QQ、银行类 App 等）不在替换范围内。
- 音量条是否有声音取决于 ColorOS 自身是否播放 `VolumePanelSound.ogg`，部分版本只在触感上反馈。
- ColorOS 16 与 17 均在一加 13 上实测通过（C17 实测命中 110/139，其余为新系统缺文件）。
- 其他 ColorOS 机型目录结构可能不同，`post-fs-data.sh` 会自动跳过不存在的目标目录，不会报错也不会破坏原文件。
- 开机后头几分钟 MediaProvider 可能尚未就绪，此时设置里的铃声列表会加载不出来，等待约 1 分钟即可，与本模块无关。

## 目录结构

```
module/                     可刷入的模块内容
  module.prop
  common.sh                 日志函数
  post-fs-data.sh           启动早期逐槽位 bind mount + SELinux 标签修正
  service.sh                启动本地 WebUI 服务（127.0.0.1:7127）
  uninstall.sh              清理日志
  customize.sh              安装脚本（保留旧选择、修正权限）
  tools/soundctl.sh         WebUI 后端：status / slots / library / set / reset / snapshot
  data/sounds.conf          当前映射（<组>/<目标文件>=<音效 id>，"-" 表示保持原声）
  data/sounds.default.conf  默认映射，供「恢复默认」使用
  webroot/                  WebUI（index.html / app.js / styles.css / theme.css）
  webroot/sounds/           212 个可选音效 + index.tsv 清单
  webroot/cgi-bin/exec      浏览器访问时的 CGI 执行入口
build/                      音频生成脚本（需要下面的音效源才能重新构建）
tools/pack.ps1              打包成 zip
```

## 重新构建

```bash
# 1. 音效源放到仓库根目录，目录名固定
git clone https://github.com/TOM-BadEN/Nintendo-Switch-Sounds-Effect
mv Nintendo-Switch-Sounds-Effect Nintendo-Switch-Sounds-Effect-main

# 2. 依赖
pip install numpy soundfile imageio-ffmpeg

# 3. 生成音效库与默认映射
cd build
python library.py

# 4. 打包
pwsh tools/pack.ps1
```

`build/library.py` 会把源包里所有含有效波形的采样编码成 ogg 音效库，并生成 `data/sounds.conf`（默认映射）。`build/build.py` 里是旧的固定槽位映射表，仍用于生成默认映射。`build/dsp.py` 是裁剪、电平与编码工具：所有输出只做三件事——裁掉首尾静音、可选的 4~6kHz 低通、峰值归一。

## 技术细节

几个踩过的坑，改这模块前值得一看：

1. **bind mount 的文件必须带 `u:object_r:system_file:s0`**。经 `adb push` 放进 `/data/adb/modules` 的文件会继承 `adb_data_file`，那个标签只给 shell/adb 用，`system_server` 和所有 App 都读不到，表现是整机静音。`post-fs-data.sh` 会在挂载前强制 `chcon`，并对 `/data/oplus` 下的目标执行 `restorecon`。
2. **`settings put system ringtone <media-uri>` 用 root 写会被静默拒绝**。Android 12+ 的 `SettingsProvider.isValidMediaUri` 需要调用方有包名，uid 0 没有，写入"成功"但值不变。必须用 shell uid（`su 2000`）执行。
3. **不要在 `su` 的手动 shell 里 `mount --bind` 做测试**，那些挂载只在当前挂载命名空间有效，退出即消失，看起来"挂上了"其实系统看不到。
4. **判定一次改动是否生效，看 `ls -Z` 和文件大小，不要只信 `mount` 命令的返回值。**
5. **ColorOS 17 把 UI 音效从 `/my_stock/media/audio/ui` 搬到了 `/my_product/media/audio/ui`**。硬编码单一路径的写法在新版本上会静默失效（日志里只有一行 `dst missing`，手机听着就是"没效果"），所以现在每组音效都配了候选列表，并把实际命中的目录打进日志。
6. **KernelSU 的 WebUI 由 `https://mui.kernelsu.org/` 这个虚拟域名提供**。在这个域名下：相对路径的 `fetch('cgi-bin/exec')` 只会拿到 CGI 脚本源码（静态文件，不会执行），必须用 `http://127.0.0.1:7127/...` 绝对地址；`ksu.exec` 的签名是 `exec(command, optionsJson, callbackName)`，回调是**全局函数名**，传函数会被静默忽略导致 Promise 永不 resolve。
7. **WebUI 的滚动容器必须自己建**。模板里的 `.app-surface` 是 `height:100vh; overflow:hidden`，内容直接塞进去会被裁掉——表现为点击有反应但完全滑不动。正确做法是让主体区域 `flex:1; min-height:0; overflow-y:auto`。
8. **`overflow-y:auto` 会让另一轴自动变成 `auto`**，只要子元素宽出一点就能左右拖。行元素用 `width:100%` + 内边距时务必配 `box-sizing:border-box`，否则正好宽出一个内边距的量。

## 音效来源与版权

- 音效来自 [TOM-BadEN/Nintendo-Switch-Sounds-Effect](https://github.com/TOM-BadEN/Nintendo-Switch-Sounds-Effect)，由 Switch 固件音频提取整理。该包 211 个文件中 204 个可用（205 个含有效波形，其中 1 个是 2ms 的空占位），其余 6 个为静音。
- Nintendo Switch 及相关音效的著作权属于任天堂。本模块仅供个人学习与自用，请勿用于商业用途或二次分发牟利。

## 更新日志

### v2.0.1

- WebUI：点音效行只**试听**，保存改为右侧独立的「使用」按钮 —— 之前点一下就会写配置，滑动时很容易误保存。
- 试听改为直接取静态文件并缓存成 blob URL，不再每次走 `base64` 的 shell 往返，点下去不再卡顿。
- 修复音效选择面板可以**左右拖动**：行元素 `width:100%` 未配 `box-sizing:border-box`，实际宽出 24px，加上 `overflow-y:auto` 会让横轴变成可滚动。
- 主列表与选择面板补 `overflow-x: hidden`、`overscroll-behavior`、长名称省略号截断。

### v2.0.0

- 新增 WebUI（Material 3 风格，与字体模块同一套设计层）。
- 音效打包成 212 个可选音效库，139 个槽位可在界面上逐个开关并自由指定音效。
- 新增 `tools/soundctl.sh` 作为 WebUI 后端，`post-fs-data.sh` 改为按 `data/sounds.conf` 逐槽位挂载。
- 新增 `service.sh` 提供本地 WebUI 服务（`127.0.0.1:7127`）。
- 移除被音效库取代的固定产物目录 `files/`。

### v1.2.0

- 适配 ColorOS 17：UI 音效迁移到 `/my_product/media/audio/ui` 后仍能生效，模块按候选目录依次探测并挂载所有实际存在的目标。
- 目标文件按绝对路径去重，避免两组音效落到同一目录时同名文件被重复挂载。
- 日志新增实际命中的目录清单与 `ok / skip / fail` 汇总，并打印第一个挂载文件的 SELinux 标签。
- `tools/pack.ps1` 改为手写 zip 条目：Windows PowerShell 的 `CreateFromDirectory` 会写出反斜杠路径，Android 解压后会得到一堆名字里带 `\` 的文件而不是目录。

### v1.1

- 移除全部合成音频：铃声（142）、天气提醒（20）、闹钟（2）、开机/关机、倒计时音全部改为保持手机原声。
- 系统 UI 音效与通知音全部使用固件原始采样，仅做裁剪与电平处理。
- 通知音去掉混响尾，改为纯峰值归一。
- 不再改写铃声 / 闹钟设置，卸载后无需还原。
- 模块体积从 33.9MB 降至 1.1MB。
- 锁屏 / 解锁改用固件原声 `StartupSleep` / `SeUnlock`。

### v1.0

- 首个版本，327 个音效全覆盖。
- 修正 SELinux 标签导致的整机静音问题。
- 修正 root 写入铃声设置被拒的问题。
- 通知音改为感知响度归一并加入削波保护。
- 重新设计锁屏/解锁三段铃音、Joy-Con 风格充电音。

## 致谢

- 「冰」的 `OnePlus13yinxiao` 模块，提供了在 ColorOS 上做音效替换的最初思路。
- [TOM-BadEN](https://github.com/TOM-BadEN) 的音效提取与整理。
