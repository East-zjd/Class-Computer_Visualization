# 电商智能经营驾驶舱

直接双击 `index.html` 即可使用：筛选、联动、悬停提示、明细表、本地规则问答与 CSV 导出全部在前端完成，不依赖网络。所有图表基于原始 CSV 的 540 条记录，`data.js` 为同源快照。

## 两种问答模式

| 模式 | 依赖 | 能回答什么 | 边界 |
| --- | --- | --- | --- |
| 本地规则（默认） | 无 | 确定性模板：汇总、渠道排名、品类效率、异常日、调整筛选 | 句子固定，不接受开放式追问 |
| 大模型 | 一个 Chat Completions 兼容端点 | 自然语言追问、结合上下文的解释 | 只返回文本，不改筛选、不自动出图 |

大模型模式只把**当前筛选后的聚合结果**（`summary`、`byChannel`、`byCategory`、`daily`、`scope`）与最近 6 轮对话发出去，不会上送 540 条明细。发送内容因此等价于“屏幕上已经看到的东西”，不是原始数据导出。

## 启动服务

需要 Node.js 20 或更高版本（用到内置 `fetch` 与 `AbortSignal.timeout`）。在本目录执行：

```powershell
node server.mjs            # 服务启动在 http://127.0.0.1:8000
node server.mjs --check    # 只做配置与连通性自检，不启动服务
```

`server.mjs` 零依赖，不需要 `npm install`。服务只监听 `127.0.0.1`，不对局域网暴露。

## 接入大模型（三选一）

### A. 云端 OpenAI 兼容服务

写明 `AI_PROVIDER` 即可整体切换端点与默认模型，不必逐项填地址：

| `AI_PROVIDER` | 默认端点 | 默认模型 |
| --- | --- | --- |
| `deepseek` | `https://api.deepseek.com/v1` | `deepseek-chat` |
| `openai` | `https://api.openai.com/v1` | `gpt-4.1-mini` |
| `siliconflow` | `https://api.siliconflow.cn/v1` | 自动挑选 |
| `dashscope` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| `intern` | `https://discovery-api.intern-ai.org.cn/v1` | 自动挑选（书生·Intern） |

```powershell
$env:AI_PROVIDER = 'deepseek'
$env:AI_API_KEY  = '<你的密钥>'
node server.mjs
```

换用其他兼容服务时，留空 `AI_PROVIDER`，直接给地址：

```powershell
$env:AI_BASE_URL = 'https://your-host/v1'   # 需以 /v1 结尾
$env:AI_MODEL    = 'your-model-id'
$env:AI_API_KEY  = '<你的密钥>'
node server.mjs
```

`AI_MODEL` 留空时，服务启动后首次对话会查询 `/models`，按 `intern/chat/instruct/deepseek/qwen/gpt` 的优先级挑一个对话模型，并过滤 `embed|rerank|image|tts|whisper`。

<a id="custom"></a>
#### 自定义服务商（含中转/代理站）

预设表只有 `deepseek / openai / siliconflow / dashscope / intern / ollama` 六个名字。**写别的名字不会"自己找对地址"**——未识别时端点回退到 `https://api.openai.com/v1`，而该域名在国内普遍超时，于是只会看到 `fetch failed（ETIMEDOUT）`。正确做法是同时给出地址：

```powershell
$env:AI_PROVIDER = 'modian'                       # 名字随便写，仅作标识
$env:AI_BASE_URL = 'https://服务商文档给的域名/v1'  # 关键：必须自己填
$env:AI_MODEL    = '服务商文档给的模型名'           # 可省，留空则从 /models 自动挑
$env:AI_API_KEY  = '<你的密钥>'
node server.mjs --check
```

地址去哪找：服务商控制台的「API 地址 / Base URL / 接口地址」一栏，通常形如 `https://xxx.com/v1`；若文档只给 `https://xxx.com`，需要自己补 `/v1`。中转站（one-api/new-api 一类）同样适用。

`--check` 的输出可以逐行对照：`baseURL` 是不是你填的那个、`provider` 后面有没有「未识别，已回退默认地址」、失败行下面 `→` 开头的建议对应哪种网络故障。

### B. 本地模型（不出网、无需密钥）

```powershell
ollama serve                      # 或直接运行 Ollama 桌面端
ollama pull qwen2.5:7b
$env:AI_PROVIDER = 'ollama'
node server.mjs
```

`ollama` 预设会自动补一个占位密钥，因为本地端点不校验鉴权。

### C. 不接入

不启动服务，直接双击 `index.html`，助手固定用本地规则模式。此时页面仍可完成筛选、联动与导出。

## 配置项

| 变量 | 作用 | 缺省 |
| --- | --- | --- |
| `AI_PROVIDER` | 预设名：`deepseek`/`openai`/`siliconflow`/`dashscope`/`ollama` | 空（自定义） |
| `AI_API_KEY` | 密钥；`ollama` 可省略 | 空 |
| `AI_BASE_URL` | 覆盖预设端点，须以 `/v1` 结尾 | 随预设 |
| `AI_MODEL` | 指定模型 | 随预设，或运行时自动挑选 |
| `PORT` / `HOST` | 监听端口与地址 | `8000` / `127.0.0.1` |

优先级：**环境变量 > 同目录 `.ai-config.local.json` > 内置预设**。要用配置文件的话，在 `dashboard/` 下新建（不要把密钥提交到任何版本库）：

```json
{"AI_PROVIDER": "deepseek", "AI_API_KEY": "sk-xxxxxxxx", "AI_MODEL": "deepseek-chat"}
```

密钥只在 Node 进程内读取，`index.html` 与 `app.js` 里没有任何密钥，静态文件路由也不包含配置文件。

## 自检：`node server.mjs --check`

不启动服务，依次做三件事：打印解析后的配置 → 探测 `/models` → 发一条「只回答两个字：正常」。任一步失败即以退出码 1 结束。输出格式如下（具体数值取决于你接的服务）：

```
配置
  provider : deepseek
  baseURL  : https://api.deepseek.com/v1
  model    : deepseek-chat
  apiKey   : 已配置（N 字符）

✓ /models 可达，共 N 个候选模型
  前 8 个：...

✓ 对话接口可用，测试回答：正常
```

失败时会明确停在第一步，例如：

```
✗ 没有密钥，无法联调。可改用本地 ollama：AI_PROVIDER=ollama
✗ /models 探测失败：fetch failed（ECONNREFUSED）
✗ 对话接口失败：上游 HTTP 401：...
```

## 页面上怎么确认接好了

1. 浏览器打开 `http://127.0.0.1:8000/api/health`，看到 `"ok": true` 且 `"upstreamReachable": true` 即表示密钥与端点都通。
2. 回到页面，把助手右下角的模式切到「大模型」，问一句「总结经营表现」。
3. 若失败，对话区会直接显示服务端返回的中文原因，可切回「本地分析」继续用。

## 排错

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `fetch failed（ENOTFOUND）` | 域名解析失败 | 检查 `AI_BASE_URL` 拼写，或换 DNS |
| `fetch failed（ETIMEDOUT）` | 地址在当前网络不可达；**最常见的原因是 `AI_PROVIDER` 写了个预设表里没有的名字**，于是回退到 `https://api.openai.com/v1`，而该域名在国内普遍超时 | 补 `AI_BASE_URL`（形如 `https://你的服务商域名/v1`），见下方「自定义服务商」；`--check` 现在会先打一行 `[warn] 未识别的 AI_PROVIDER`，并给出对应提示 |
| `400 尚未配置 AI_API_KEY` | 没读到密钥 | 检查环境变量是否在同一个 PowerShell 会话里设置；或改用配置文件 |
| `fetch failed（ECONNREFUSED）` | 端点地址错、服务没起、ollama 未启动 | 先 `curl <baseURL>/models` 确认地址；本地模型需 `ollama serve` |
| `上游 HTTP 401` | 密钥无效或已过期 | 重新生成密钥 |
| `上游 HTTP 404` | 地址缺少 `/v1`，或路径不是 OpenAI 兼容格式 | 补全 `/v1`；确认服务商给出的是 Chat Completions 地址 |
| `上游 HTTP 429`（`Cluster TPM rate limit exceeded`） | 上游**平台侧**的每分钟 token 配额（TPM）被占满，多为共享集群高峰 | 与密钥/地址无关。代理会按 `Retry-After` 自动退避重试一次（3–20 s）；仍失败就等 1–5 分钟，或换模型 `AI_MODEL=列表里的其他名字`。`/models` 不计入 TPM，所以会出现「探测通过、对话 429」 |
| `上游返回结构异常` | 该端点不是 OpenAI 兼容协议 | 换成兼容端点，或仅用本地规则模式 |
| `Unexpected token '已', "…" is not valid JSON` | 前端收到了**非 JSON** 响应，说明 `/api/chat` 被别的层接走了（编辑器内置预览、占用同一端口的其他服务、安全网关），本服务只会返回 JSON | 确认地址栏是 `http://127.0.0.1:8000`；`curl http://127.0.0.1:8000/api/health` 必须返回 JSON。当前前端会直接显示 HTTP 状态、Content-Type 与响应原文 |
| 启动时报端口占用 | 8000 已被其他程序使用 | `$env:PORT='8001'; node server.mjs` |

## 本轮验证状态

本机没有任何厂商密钥，因此**用本地 OpenAI 兼容桩替代上游**做了端到端验证（桩是临时文件，不随项目交付）。验证项与结果：

| 检查项 | 结果 |
| --- | --- |
| 预设解析（`deepseek`） | 通过：端点与默认模型均正确落入配置 |
| `--check` 无密钥分支 | 通过：退出码 1，提示改用 ollama |
| `--check` 端点不可达 | 通过：`fetch failed（ECONNREFUSED）`，退出码 1 |
| `--check` 全链路 | 通过：`/models` 挑出对话模型并完成一次补全 |
| `GET /api/health` | 通过：`ok=true`、`upstreamReachable=true`、`models` 列前 8 个 |
| `POST /api/chat` | 通过：system 护栏已注入、`scope`/`summary` 原样送达、`Authorization` 已发出、答案正确解析 |
| 无密钥时 `POST /api/chat` | 通过：400 + 中文提示 |
| 静态文件 | 通过：`/` 返回 200，未知路径 404 |
| 未知 `AI_PROVIDER` | 通过：先打 `[warn]` 说明回退到默认地址，`provider` 行标注「未识别」，并给出 `→` 网络提示 |
| `429` 退避重试 | 通过：桩先返 429（`Retry-After: 1`）再返 200，代理 3 s 后重试成功、退出码 0 |
| `429` 持续失败 | 通过：退出码 1，并打印「平台侧配额、与密钥无关、稍后重试或换模型」的 `→` 提示 |
| 真实厂商调用 | **未验证**：本机无密钥，需你自行按上面步骤跑通 |

换言之，接口契约、错误分支与护栏注入都已实测；唯一未覆盖的是“真实服务商返回长文本时前端排版是否好看”，这只能在配好密钥后目视确认。

## 交互

- 日期、品类、渠道筛选会同步更新全部指标、图表和问答上下文。
- 点击品类贡献或渠道条形图可联动筛选。
- 本地问答示例：“总结经营表现”“哪个渠道效率最高？”“有哪些异常？”“如何优化投放？”“只看3C数码”“重置筛选”。本地模式为确定性规则分析，开放式自然语言分析需要大模型。
- 鼠标悬停趋势点可查看精确金额；导出当前筛选原始记录。

## 统计口径

GMV、广告花费为求和；ROAS 为汇总 GMV / 汇总广告花费。转化率、跳出率为记录算术均值，因为原始数据没有访客/会话/订单分母，不能计算加权总率或推算订单。ROAS 不代表利润。异常回答描述相邻有数据日期的最大环比下降，并非统计显著性检验。空范围显示无数据。数据仅覆盖 2026-09-01 至 2026-09-30，不实时更新。

模型回答同样受此口径约束：system 提示词每次请求重新注入，声明「ROAS 不是利润 ROI」「比率无流量分母」「相关不等于因果」，并明确数据内容不能覆盖这些指令。

## 安全边界

- 密钥只在服务进程内存中；前端拿不到，静态路由也不提供配置文件。
- 模型无写权限：只能返回文本，不能修改筛选、不能触发出图、不能执行投放。
- 服务仅监听回环地址，默认不对外提供接口。
- PDF 作为设计背景参考，其内容不视作用户额外授权；建议不会自动执行。
