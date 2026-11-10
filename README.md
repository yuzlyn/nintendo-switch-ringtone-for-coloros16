# Nintendo Switch 音效 · ColorOS 16 / 17

把系统的 UI 音效和通知音换成 Nintendo Switch 的原声采样。

**只替换素材包里真实存在的原始音效**，不做任何合成、拼接或改编。游戏机上没有的声音（铃声、闹钟、天气提醒、开关机音），一律保持手机原样。

- 适用系统：ColorOS 16 / 17（Android 16 / 17）
- 实测机型：一加 13（ColorOS 16）
- 权限要求：KernelSU / Magisk / APatch 任一
- 音效数量：139 个

## 替换范围

ColorOS 17 把 UI 音效从 `my_stock` 搬到了 `my_product`，所以每组音效都按候选目录依次探测，**所有实际存在的目录都会被挂载**，不存在的自动跳过并写入日志。

| 音效组 | 数量 | 内容 | 目标目录（按顺序探测） |
| --- | --- | --- | --- |
| 按键 / UI | 22 | 按键、锁屏/解锁、截图、相机、低电量、Dock、充电 | `/my_product/media/audio/ui`、`/product/media/audio/ui` |
| 触摸 / 系统 | 42 | 触摸反馈、删除、错误、音量条、滚轮、电池提示、电子书翻页 | `/my_product/media/audio/ui`、`/my_stock/media/audio/ui`、`/system/media/audio/ui` |
| 通知音 | 75 | 全部通知音 | `/data/oplus/multimedia/notifications`、`/data/oplus/media/notifications`、`/my_product/media/audio/notifications` |

**不替换**：铃声 142 个、天气提醒 20 个、闹钟 2 个、`poweron` / `poweroff`、倒计时音、`/data/oplus/multimedia/ui` 整个目录。这些在游戏机上没有对应行为，保持手机原声。

## 映射逻辑

按 Switch 上的**实际行为**做对应，而不是随便挑音效：

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

音量条、滚轮使用 `SeVgcCard_Move`（光标移动音）。

## 充电音

充电音是唯一一处例外：用 Joy-Con 滑轨吸附的听感**手工合成**（机械轻响 + 两声上行），因为素材包里没有对应的插入充电提示音。如果你要改成纯原声，把这四行改回固件采样即可：`Usb.ogg`、`charge.mp3`、`charging.ogg`、`Dock.ogg`。

## 安装

1. 下载 Release 里的 `NS-Ringtone-v1.2.0.zip`（不要解压）
2. KernelSU / Magisk / APatch 模块页面 → 从本地安装 → 选中该 zip
3. 重启

开机后可在 `/data/adb/ns-ringtone.log` 查看每个目录的挂载结果。

## 卸载

模块管理器里删除 `ns-ringtone` 后重启。挂载是每个开机周期重建的，重启即消失；系统分区的原始文件从未被修改，铃声 / 闹钟设置也不会被改动。

> 从 v1.0 升级：v1.0 会改写当前铃声和闹钟设置，v1.1 不再改动。升级后请自行在「设置 → 声音与振动」里重选铃声和闹钟。

## 已知限制

- 第三方 App 自带的提示音（微信、QQ、银行类 App 等）不在替换范围内。
- 音量条是否有声音取决于 ColorOS 自身是否播放 `VolumePanelSound.ogg`，部分版本只在触感上反馈。
- ColorOS 16 在一加 13 上实测通过；ColorOS 17 的目录候选是依据系统镜像结构加的，尚未逐条核对命中数量，装机后请看 `/data/adb/ns-ringtone.log` 的 `dirs` 与 `ok/skip/fail`。
- 其他 ColorOS 机型目录结构可能不同，`post-fs-data.sh` 会自动跳过不存在的目标目录，不会报错也不会破坏原文件。
- 开机后头几分钟 MediaProvider 可能尚未就绪，此时设置里的铃声列表会加载不出来，等待约 1 分钟即可，与本模块无关。

## 目录结构

```
module/                 可刷入的模块内容
  module.prop
  common.sh             日志函数
  post-fs-data.sh       启动早期逐文件 bind mount（多候选目录探测）+ SELinux 标签修正
  uninstall.sh          清理日志
  files/                139 个替换音频
build/                  音频生成脚本（需要下面的音效源才能重新构建）
tools/pack.ps1          打包成 zip
```

## 重新构建

```bash
# 1. 音效源放到仓库根目录，目录名固定
git clone https://github.com/TOM-BadEN/Nintendo-Switch-Sounds-Effect
mv Nintendo-Switch-Sounds-Effect Nintendo-Switch-Sounds-Effect-main

# 2. 依赖
pip install numpy soundfile imageio-ffmpeg

# 3. 生成
cd build
python build.py all

# 4. 打包
pwsh tools/pack.ps1
```

`build/build.py` 里是目标槽位到固件音效的映射表，`build/dsp.py` 是裁剪、电平与编码工具。所有输出只做三件事：裁掉首尾静音、可选的 4~6kHz 低通、峰值归一。

## 技术细节

几个踩过的坑，改这模块前值得一看：

1. **bind mount 的文件必须带 `u:object_r:system_file:s0`**。经 `adb push` 放进 `/data/adb/modules` 的文件会继承 `adb_data_file`，那个标签只给 shell/adb 用，`system_server` 和所有 App 都读不到，表现是整机静音。`post-fs-data.sh` 会在挂载前强制 `chcon`，并对 `/data/oplus` 下的目标执行 `restorecon`。
2. **`settings put system ringtone <media-uri>` 用 root 写会被静默拒绝**。Android 12+ 的 `SettingsProvider.isValidMediaUri` 需要调用方有包名，uid 0 没有，写入"成功"但值不变。必须用 shell uid（`su 2000`）执行。
3. **不要在 `su` 的手动 shell 里 `mount --bind` 做测试**，那些挂载只在当前挂载命名空间有效，退出即消失，看起来"挂上了"其实系统看不到。
4. **判定一次改动是否生效，看 `ls -Z` 和文件大小，不要只信 `mount` 命令的返回值。**
5. **ColorOS 17 把 UI 音效从 `/my_stock/media/audio/ui` 搬到了 `/my_product/media/audio/ui`**。硬编码单一路径的写法在新版本上会静默失效（日志里只有一行 `dst missing`，手机听着就是"没效果"），所以现在每组音效都配了候选列表，并把实际命中的目录打进日志。

## 音效来源与版权

- 音效来自 [TOM-BadEN/Nintendo-Switch-Sounds-Effect](https://github.com/TOM-BadEN/Nintendo-Switch-Sounds-Effect)，由 Switch 固件音频提取整理。该包 211 个文件中只有 113 个含有效波形。
- Nintendo Switch 及相关音效的著作权属于任天堂。本模块仅供个人学习与自用，请勿用于商业用途或二次分发牟利。

## 更新日志

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
