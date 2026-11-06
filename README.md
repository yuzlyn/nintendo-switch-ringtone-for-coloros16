# Nintendo Switch 音效 · ColorOS 16

把整机的系统音效换成 Nintendo Switch 的声音：开机、关机、锁屏、解锁、按键、充电、通知、铃声、闹钟、天气提醒。

模块用 bind mount 覆盖原文件，**不改动系统分区里的任何原始文件**，卸载后重启即完全还原。

- 适用系统：ColorOS 16（Android 16）
- 实测机型：一加 13
- 权限要求：KernelSU / Magisk / APatch 任一
- 音效总数：327 个

## 替换范围

| 目录 | 数量 | 内容 |
| --- | --- | --- |
| `/product/media/audio/ui` | 22 | 按键、锁屏/解锁、快门、对焦、低电量、截图、充电、Dock |
| `/my_stock/media/audio/ui` | 66 | 开机 `poweron.mp3`、关机 `poweroff.mp3`、触摸反馈、删除、错误、音量条、滚轮、天气提醒 |
| `/data/oplus/multimedia/ui` | 20 | 天气提醒 |
| `/data/oplus/multimedia/ringtones` | 142 | 全部铃声 |
| `/data/oplus/multimedia/notifications` | 75 | 全部通知音 |
| `/my_stock/media/audio/alarms` | 2 | 闹钟 |

装了模块后，系统设置里当前选中的铃声 / 闹钟 / 通知会被切到已替换的条目；原选择会备份到 `/data/adb/ns-ringtone/`，卸载时自动还原。

## 安装

1. 下载 Release 里的 `NS-Ringtone-v1.0.zip`；
2. 在 KernelSU / Magisk 的模块页面选择"从本地安装"，选中该 zip；
3. 重启。

开机后可以从 `/data/adb/ns-ringtone.log` 看到每个目录的挂载结果。

## 卸载

在模块管理器里删除 `ns-ringtone` 后重启。挂载随重启消失，铃声设置由 `uninstall.sh` 还原。

## 音效说明

- **系统音效**：取自 Nintendo Switch 固件提取的 211 个原始音效（其中 113 个含有效波形），按键、焦点移动、确认、错误、Joy-Con 连接、睡眠、eShop / 相册 / 新闻启动音等。
- **铃声、闹钟、天气提醒**：Switch 并没有"铃声"素材，这部分是按 Switch 的音色特征（清脆铃音、三角波贝斯、五声音阶、五度跳进）生成的原创 chiptune，共 12 种风格 × 12 个调性，用于填满 142 个铃声槽位。
- **开机 / 关机音**：按 Switch 启动 chime 的听感单独合成，各 5.8 秒。
- **锁屏 / 解锁**：三段式上行、下行铃音。
- **充电音**：模拟 Joy-Con 滑轨吸附，机械轻响加两声上行。

## 已知限制

- 第三方 App 自带的提示音（微信、QQ、银行类 App 等）不会被替换，它们不走系统音效文件。
- 音量条是否有声音取决于 ColorOS 自身是否播放 `VolumePanelSound.ogg`，部分版本只在触感上反馈。
- 铃声列表里的名称保持原样（Apex、Bark、ringtone_001 等），只替换了文件内容，避免改动 MediaStore 记录导致已选铃声失效。
- 只在 ColorOS 16 的一加 13 上验证过。其他 ColorOS 机型目录结构可能不同，`post-fs-data.sh` 会自动跳过不存在的目标目录。

## 目录结构

```
module/                 可刷入的模块内容
  module.prop
  common.sh             公共函数（MediaStore 查询、以 shell uid 写设置）
  post-fs-data.sh       启动早期逐文件 bind mount + SELinux 标签修正
  service.sh            开机后把铃声/闹钟指向 Switch 条目（每个版本只执行一次）
  uninstall.sh          还原原始铃声选择
  files/                327 个替换音频
build/                  音频生成脚本（需要下面的音效源才能重新构建）
tools/pack.ps1          打包成 zip
```

## 重新构建

```bash
# 1. 把音效源放到仓库根目录，目录名固定
#    https://github.com/TOM-BadEN/Nintendo-Switch-Sounds-Effect
git clone https://github.com/TOM-BadEN/Nintendo-Switch-Sounds-Effect
mv Nintendo-Switch-Sounds-Effect Nintendo-Switch-Sounds-Effect-main

# 2. 依赖
pip install numpy soundfile imageio-ffmpeg

# 3. 生成（ui = 系统音效，notif = 通知，tones = 铃声与闹钟，all = 全部）
cd build
python build.py all

# 4. 打包
pwsh tools/pack.ps1
```

`build/music.py` 是 chiptune 生成器，`build/dsp.py` 是合成与电平处理工具，`build/ringtones.txt` 是 142 个铃声槽位的文件名清单。

## 技术细节

几个踩过的坑，改这模块前值得一看：

1. **bind mount 的文件必须带 `u:object_r:system_file:s0`**。经 `adb push` 放进 `/data/adb/modules` 的文件会继承 `adb_data_file`，那个标签只给 shell/adb 用，`system_server` 和所有 App 都读不到，表现是整机静音。`post-fs-data.sh` 会在挂载前强制 `chcon`，并对 `/data/oplus/multimedia` 下的目标执行 `restorecon`，把它们恢复成 `oplus_multimedia_file`。
2. **`settings put system ringtone <media-uri>` 用 root 写会被静默拒绝**。Android 12+ 的 `SettingsProvider.isValidMediaUri` 需要调用方有包名，uid 0 没有，写入"成功"但值不变。必须用 shell uid（`su 2000`）执行。
3. **不要在 `su` 的手动 shell 里 `mount --bind` 做测试**，那些挂载只在当前挂载命名空间有效，退出即消失，看起来"挂上了"其实系统看不到。

## 音效来源与版权

- 系统音效来自 [TOM-BadEN/Nintendo-Switch-Sounds-Effect](https://github.com/TOM-BadEN/Nintendo-Switch-Sounds-Effect)，由 Switch 固件音频提取整理。
- Nintendo Switch 及相关音效的著作权属于任天堂。本模块仅供个人学习与自用，请勿用于商业用途或二次分发牟利。
- 铃声部分为原创编曲，不包含任何游戏原曲旋律。

## 更新日志

### v1.0

- 首个版本，327 个音效全覆盖。
- 修正 SELinux 标签导致的整机静音问题。
- 修正 root 写入铃声设置被拒的问题。
- 通知音改为感知响度归一（RMS -13.5dB），并加入削波保护。
- 点击音改用 Switch 唤醒画面的按键音，取消高频成分过重的短点击。
- 重新设计锁屏/解锁三段铃音、Joy-Con 风格充电音。

## 致谢

- 「冰」的 `OnePlus13yinxiao` 模块，提供了在 ColorOS 上做音效替换的最初思路。
- [TOM-BadEN](https://github.com/TOM-BadEN) 的音效提取与整理。
