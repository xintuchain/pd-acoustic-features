# PD Acoustic Features

**语音声学特征提取工具包** — 输入音频文件，输出标准的 jitter / shimmer / HNR / F0 声学特征。

> ⚠️ **本工具仅供研究 / 个人声音特征追踪用途，不是医疗诊断工具。**
> 它不从音频中判断任何疾病，不输出"是否患有某种疾病"的结论，也不能替代临床评估。
> 本仓库为**免费版**（特征定义 + 单文件最小示例 + UCI 复现步骤）；**完整源码（`src/` 包、`tests/` 自测、HTTP 服务封装、完整文档与 DISCLAIMER）见付费版。**

**English:** PD Acoustic Features (free edition) is a lightweight Python toolkit that extracts standard acoustic perturbation features (jitter, shimmer, HNR, F0) from voice recordings. It is built on **parselmouth** (the Python interface to Praat) and released under **GPL-3.0-or-later** by LONGAID. **Research / personal voice-tracking use only — it is not a medical diagnostic tool, does not infer any disease from audio, and cannot replace clinical assessment.** This repo is the free edition (feature definitions + one single-file runnable example + UCI reproduction steps); the full source package, tests, HTTP server and full documentation are in the paid edition.

---

## 这是什么

一个轻量的 Python 工具（本仓库为免费版，提供一个**可单独运行的最小示例** `pd_acoustic_features.py`），把语音音频转换成一组**已被广泛研究的声学扰动特征**：

| 特征 | 含义 | 单位 | 实现（Praat / parselmouth） |
|:--|:--|:--|:--|
| `jitter_local` | 局部基频周期扰动 | ratio | `Get jitter (local)`；周期 0.1–20 ms，最大周期因子 1.3 |
| `jitter_rap` | 3 点相对平均基频扰动 | ratio | `Get jitter (rap)`；参数同上 |
| `jitter_ppq5` | 5 点基频扰动商 | ratio | `Get jitter (ppq5)`；参数同上 |
| `shimmer_local` | 局部幅度扰动 | ratio | `Get shimmer (local)`；最大幅度因子 1.6 |
| `shimmer_db` | 幅度扰动 | dB | `Get shimmer (local_dB)`；参数同上 |
| `hnr_mean` | 谐噪比均值 | dB | `To Harmonicity (cc)`（时间步 0.01 s，最低基频 75 Hz）→ `Get mean` |
| `f0_mean` | 基频均值 | Hz | `To Pitch`（75–600 Hz）→ 有声帧均值 |
| `f0_sd_semitone` | 基频标准差 | semitone | `To Pitch` → 逐帧 `12·log2(F0/27.5)` 的标准差 |

底层使用开源的 **parselmouth**（Praat 的 Python 接口），无需商业软件、无需临床设备。

> ⚠️ **许可提示**：parselmouth 封装 Praat，以 **GPL-3.0** 发布；因此本工具整体以 **GPL-3.0-or-later** 发布（详见下方「许可与引用」）。

## 适合谁

- 做**声音健康监测**研究、但不想从零实现声学特征提取的开发者
- 需要**批量提取语音声学特征**用于建模的研究者
- 想在自己的 App / 服务里加一个"声音特征"模块的创业者

## 不适合谁

- 想用它**诊断疾病**的人 —— 请咨询专业医疗机构
- 需要**临床级精度**的场景 —— 本工具基于开源特征集，非临床设备

---

## 安装

```bash
pip install praat-parselmouth soundfile numpy
```

> PyPI 包名是 **`praat-parselmouth`**（代码里 `import parselmouth` 不变）；包内已含预编译的 Praat 二进制，跨平台（macOS / Linux / Windows）。

## 用法

免费版提供**单文件最小示例** `pd_acoustic_features.py`（只依赖 parselmouth + numpy，可单独运行）：

```bash
python pd_acoustic_features.py voice.wav
```

```json
{"file": "voice.wav", "jitter_local": 0.0021, "shimmer_db": 0.134, "hnr_mean": 18.42, "f0_mean": 198.31, "f0_sd_semitone": 0.87}
```

也可在同文件内作为库调用：

```python
from pd_acoustic_features import extract_acoustic_features

feats = extract_acoustic_features("voice.wav")
```

> `src/` 完整包（`extract_batch`、HTTP 服务封装 `server.py`、`tests/` 自测脚本、完整文档与 DISCLAIMER）见**付费版**。

## 数据格式建议

- **WAV**，单声道，16 kHz 或以上采样率效果最好
- 一段**持续元音**（如发 /a/ 3-5 秒）能得到最稳定的 jitter / shimmer；**注意**：这里的「稳定」指同一录音条件下的**可重复性**（信度），**不代表这些特征能反映疾病或严重度**（效度未验证）
- 连续语音亦可，但特征方差会更大
- 安静环境录制（背景噪声会拉低 HNR）
- **不同录音协议能支持的结论不同**：朗读、自由说话、持续元音各自支持的推理不同（本工具只输出特征值，不跨协议下患病判断）
- **本工具不对输入做降噪或增强**：自行降噪 / 增强会改变 jitter / shimmer / HNR，处理前后的结果不可直接比较

---

## 验证状态（诚实披露）

本工具的方法论已在公开数据集上验证：

- 使用 **UCI Parkinson's 语音数据集**（195 条，147 PD + 48 HC）
- **UCI 数据集自带的 22 个 MDVP 特征（原作者提取，非本工具输出）** 中，**21 个在 PD 组 vs 健康对照间 p < 0.01**（20 个 p < 0.001）
- 本工具对**同名特征只做方向对照**（不同工具的同名特征不可直接比数值，见局限 4）；特征变化**方向与已发表文献一致**（如 jitter、shimmer 升高，HNR 降低）
- **本验证只做逐特征组间检验，没有挑特征或挑阈值，不涉及嵌套选择**

### UCI 数据集的下载与复现

- **数据**：UCI Machine Learning Repository — *Parkinson's Disease*（195 条录音，147 PD + 48 对照，22 个 MDVP 特征）
  URL: <https://archive.ics.uci.edu/dataset/174/parkinsons>
- **复现步骤**：
  1. `pip install praat-parselmouth soundfile numpy pandas`
  2. 从上面链接下载数据文件（`parkinsons.data` / CSV）
  3. 用本仓库 `pd_acoustic_features.py` 对自己的录音提取特征；与 UCI 的 22 个 MDVP 特征只做**方向对照**（不同工具的同名特征不可直接比数值，见下方局限 4）
  4. 组间比较（PD vs 对照）建议按**受试者**聚合后统计，并报告最差子群体（无分组信息时注明「未做子群体检验」）

**技术成熟度（TRL）**

| 维度 | 等级 | 说明 |
|:--|:--|:--|
| 方法论 | **TRL 4-5** | jitter/shimmer/HNR 与 PD 的组间差异有公开数据支持（UCI，探索性，见局限 9）；本工具输出本身尚未在患者录音上验证 |
| 工程可用性 | **TRL 3-4** | 依赖开源 parselmouth（Praat），未在临床级设备环境验证 |

**已知局限（重要）**

1. 目前主要在**合成测试音频 + UCI 预提取特征**上验证；尚未在大规模**真实患者短录音**上系统验证
2. 输出的是**声学量**，不是诊断结论；组间统计差异 ≠ 个体诊断能力
3. 单一录音的绝对数值受麦克风、环境噪声、录音距离影响，**建议关注同一人多次录音的相对变化**，而非单次绝对值
4. ⚠️ **跨工具不可直接比较**：不同工具包（openSMILE / Praat / librosa）即使参数对齐，同名特征也可能显著不一致。已发表评估（Choi et al., arXiv:2506.01129）显示 F0 百分位跨工具高度一致（r=0.96–0.999），但 **F0 标准差与共振峰一致性差甚至负相关**。本工具的 `f0_sd_semitone` 属该风险类别，跨平台复现时请谨慎解释。本系列数值**仅在本工具内部可比**。
5. `shimmer_local`（比例）与 `shimmer_db`（分贝）是两个独立量，分别来自 Praat "Get shimmer (local)" 与 "Get shimmer (local_dB)"，勿混用
6. 未提供：说话人分离、情感识别、语言内容理解
7. ⚠️ **单次录音受用药状态影响**：MGH Neurobooth 纵向研究（Chandra 2026）发现，在无用药监督下模型即可分离药理学状态——**OFF 态预测严重度显著高于 ON 态**（p=0.003）。同一人不同用药时点的录音**不可直接比较**，建议记录用药时点（与「固定时段采集」结合）
8. ⚠️ **组间分离 ≠ 严重度预测**：BRAINPHONE 俄罗斯队列（n=201）显示，jitter/shimmer/HNR 类特征可**语言宽容地**分离 PD 与对照，但与临床严重度的相关性很弱（|ρ| ≤ ~0.21，未过 FDR）。不要把「能区分组」理解为「能预测病情程度」
9. ⚠️ **按录音统计 + 数据集混杂**：UCI 数据（含本 README 的验证结论）按**录音条数**而非**受试者**统计，同一名受试者的多条录音会同时进入组间比较，独立性被高估，显著性可能偏乐观（同一现象见局限第 10 条）。更严重的是，近期研究（Jouaiti & Ma, IEEE SLT 2026，arXiv:2609.21080）系统排查多个临床语音数据集（含帕金森库 Neurovoz、MDVR-KCL）发现：**只用静音片段训练的分类器，其表现常追平甚至超过完整音频**——即数据集本身存在「只用旁门线索也能分对」的混杂风险。因此本工具在 UCI 上的 p 值应视为**探索性**结论，不能当作临床证据。
10. ⚠️ **重复录音的有效样本量远小于名义数量**：UCI 纵向数据集名义 5875 条记录实际来自 42 名患者，患者身份解释约 77% 的方差（Chauhan 2026，Digital Health），校正依赖后有效独立观测约 54。用重复录音做统计时请勿直接以记录条数计 N
11. ⚠️ **高准确、"组间无差异"均不足以证明稳健**：受控声学干预研究（arXiv:2610.01846）显示，噪声/混响能系统性地改变疾病预测，而该声学因素在原数据里**组间并无显著差异**；反之，单一高分也不能证明特征抓到了疾病机制。判断稳健要**连同方差源（种子 / 子群体 / 说话人 / 协议）一起报告**，而非只看一个点估计。
12. ⚠️ **手工特征在跨说话人分类上不如自监督表征**：清醒开颅构音障碍研究（arXiv:2610.11825）发现，跨说话人任务中多层自监督表征比传统手工声学描述子 AUC 高 18.2%–26.1%。**本工具卖的是可解释的特征值，不追求分类性能**，不可声称手工特征上能与 SSL 表征竞争。
13. ⚠️ **特征值对录音条件敏感（待补漂移表）**：同一段语音在不同信噪比 / 混响下的特征漂移幅度尚未系统量化；漂移大的特征将在本 README 标注「对录音条件敏感」。（计划于 10-31 前补一次「录音条件扰动检验」）
14. ⚠️ **未做子群体检验**：UCI 该数据集不提供年龄/性别等分组信息，故未做「最差子群体指标」检验；不为此另找数据。

## 免费版 vs 付费版

本工具同时提供**免费版**和**付费版**，两者差在“交付形态”，不在“能不能用”：

| | 免费版（GitHub 公开仓库） | 付费版（面包多：https://mbd.pub/o/bread/YZaVmZ9yZA==） |
|:--|:--|:--|
| 特征定义表 + 使用说明 | ✅ | ✅ |
| 一段最小可运行示例 | ✅ | ✅ |
| UCI 数据集下载链接与复现步骤 | ✅（不放数据文件本身） | ✅ |
| `src/` 完整源码（可离线运行） | — | ✅ |
| `examples/` 完整示例 + `tests/` 自测脚本 | — | ✅ |
| HTTP 服务封装（`server.py`） | — | ✅ |
| 完整 README（逐特征定义 / 验证状态 / 已知局限） + DISCLAIMER | — | ✅ |
| 一次性买断 · 本地运行 · 音频不出本机 | — | ✅ |

**为什么要设付费版：** 第一阶段我们要验证一个假设——「是否有人愿意为可复现的科研代码付钱」。免费版足以让人判断工具是否适合自己；如果它确实省下了你搭 parselmouth/Praat 环境、对齐特征定义的时间，欢迎用 1 元支持，并帮我们验证这个假设。购买页：https://mbd.pub/o/bread/YZaVmZ9yZA==

## 与云端语音 API 的差异

本工具是**本地运行的开源库**，与商业云端语音分析 API 的定位不同：

| 维度 | 本工具 | 云端语音 API（如生物标志物类服务） |
|:--|:--|:--|
| 运行位置 | **本地进程内** | 需上传音频到服务商服务器 |
| 计费 | 一次性 / 无按量费 | 按用量或企业档（参考量级：事件分类约 $0.02/小时；企业语音生物标志物 API 档数千美元） |
| 访问门槛 | 无 | 多数需组织审批与 API key |
| 隐私 | 音频不出本机 | 音频离开本机（依赖服务商合规） |
| 输出 | 声学量（可解释） | 常为黑箱风险评分 |

**何时选本工具**：需要**可解释的声学量**、**数据不出本机**、**无按量成本**、需要嵌入自有研究/工程管道时。
**何时选云端 API**：需要**开箱即用的疾病风险评分**、不具备本地部署条件、或需要厂商承担合规责任时。

> 定价参考仅供定位对比，非本产品定价建议。

## 许可与引用

- 本工具以 **GNU GPL v3.0 或更高版本（GPL-3.0-or-later）** 发布（见 [LICENSE](LICENSE)），署名 LONGAID。
- 本工具底层使用 **parselmouth**（[Praat](https://www.fon.hum.uva.nl/praat/) 的 Python 接口，GPL-3.0）。parselmouth 由 Yannick Jadoul 维护；Praat 由 Paul Boersma 与 David Weenink（阿姆斯特丹大学）开发。
- 采用 GPL-3.0 的原因：parselmouth 以 GPL-3.0 发行，本工具调用它，整体需以兼容许可证发布。
- 特征定义与实现跟随 Praat 官方定义；学术工作中建议引用 Praat，以及相关声学参数的原始文献（jitter / shimmer / HNR 的 MDVP 与 Praat 定义）。

## 免责声明

**本工具明确不用于疾病诊断或临床决策，只输出声学特征值。**（完整免责声明 DISCLAIMER 见付费版。）
