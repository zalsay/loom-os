# 项目格式

`new_episode.py` 生成模板；填写后用 validate 检查，只有占位文字消除后才可渲染。

## episode.json

顶层：`episode_id`（英文小写/数字/连字符）、`revision`（正整数）、`kind`、`topic`、`header`、`source_notes`（来源列表）、`voice`、`scenes`。

`voice`：`model`、`voice`、`direction`。每个场景：`type`、`duration`、`title`（最多两行）、`caption`（最多两行）、`body`（卡片或标签文字）、`illustration`（car/garden/generic）、`narration`（逐字稿，可为空）、`evidence`（实际来源）。对比场景另设 `before`、`after`（最多三行），标签可用 `before_label`、`after_label`。

每个镜头2–30秒，总长2–180秒，精确到24fps整数帧。默认约60秒。标题每行≤13字，字幕≤17字；正文一般≤14字/最多5行。idea≤7字×2行，ai≤10字×3行，garden≤9字×4标签，growth/end≤14字×2行，test≤14字×4行，compare两卡各≤8字×3行。这些是预置布局限制，特殊镜头可修改渲染器与验证规则后重新视觉检查。

| 场景 | 内容 |
| --- | --- |
| idea | 孩子思考，提出问题，展示相关对象 |
| build | 方案卡片、孩子动手与作品示意 |
| test | 运行轨迹和实际观察卡片；轨迹只是示意 |
| compare | 两个方案或前后观察对比，以来源解释差异 |
| ai | 孩子思考、问题、共同尝试；界面标“交互示意” |
| garden | 四个个人移动种植格，标签可改 |
| growth | 植物与根系显现，观察文字可改 |
| record | 观察/测试记录、相关对象 |
| end | 暖金大字织界、固定教学表达、下一步 |

场景库仅提供布局和原创图元；若本期结构或证据不同，要修改复制到本期目录中的 `render_episode.cjs`，不能以示意图证明实际结果。真实素材镜头可新增独立渲染逻辑，保留顶部留白与字体规则。

同一期递增revision；新一期新episode_id。旁白指纹包括文本、风格、模型、音色和窗口。`release.json` 的visual_review与listening_review由完成对应人工检查后更新，不能把pending改成passed来跳过检查。
