# 随机点名系统 重构 & 功能扩展 设计文档

**日期：** 2026-05-02  
**方案：** 渐进式重构（方案 A）——先分层修 Bug，再在新结构上追加新功能  
**目标平台：** Windows 7+，打包为单 exe，U 盘可直接运行

---

## 一、项目结构

```
order_name/
├── main.py                        # 入口，仅 ~10 行
├── app/
│   ├── config.py                  # 全局配置（数据路径等）
│   ├── data/
│   │   ├── models.py              # 数据类：Student, Record, ClassData
│   │   ├── repository.py          # JSON 读写、路径管理、原子写
│   │   └── migration.py           # v1 → v2 迁移逻辑
│   ├── logic/
│   │   ├── roll_call.py           # 随机抽取、轮询状态管理
│   │   └── statistics.py          # 统计计算（次数、均分）
│   └── ui/
│       ├── main_window.py         # 主窗口、Tab 容器、班级工具栏
│       ├── tab_roll_call.py       # 随机点名 Tab
│       ├── tab_students.py        # 学生管理 Tab
│       ├── tab_records.py         # 记录查询 Tab
│       ├── tab_stats.py           # 统计图表 Tab（新增）
│       ├── dialogs/
│       │   ├── class_dialog.py    # 班级增删改对话框
│       │   └── settings_dialog.py # 数据路径设置对话框
│       └── widgets/
│           ├── animation_widget.py # 抽签滚动动画
│           └── status_panel.py     # 已点/未点状态面板
├── assets/
│   ├── 2026上人力资源管理概论课-工商管理班学生名单-导入用.xlsx
│   └── 2026上人力资源管理概论课-市场营销班学生名单-导入用.xlsx
└── data/                          # 运行时生成，默认与 exe 同目录
    └── roll_call_data.json
```

**分层原则：**
- `data/` 层无 PyQt5 依赖，只负责读写 JSON
- `logic/` 层无 PyQt5 依赖，只做计算
- `ui/` 层只调用 `logic/` 和 `data/`，不直接操作 JSON

---

## 二、数据模型 & 向下兼容

### 新版 JSON 格式（v2）

```json
{
  "version": 2,
  "classes": [
    {
      "id": "cls_001",
      "name": "工商管理班",
      "students": [
        {"id": "2541123101", "name": "曾璟宁", "status": "normal"}
      ],
      "records": [
        {
          "student_id": "2541123101",
          "name": "曾璟宁",
          "time": "2026-05-02 10:00:00",
          "score": 85,
          "status": "normal"
        }
      ],
      "called_ids": ["2541123101"]
    }
  ],
  "settings": {
    "data_path": ""
  }
}
```

### 与旧版（v1）差异

| 字段 | v1 | v2 |
|------|----|----|
| 版本标记 | 无 | `"version": 2` |
| 班级组织 | 顶层四个平行 dict，以班级名为 key | 每个班级为独立对象，含 `id` + `name` |
| 学生状态 | 无 | `"status": "normal" \| "absent" \| "leave"` |
| 已点名列表 | 存完整 student 对象 | 只存 `student_id` 字符串 |
| 统计聚合键 | 按姓名（存在同名 Bug） | 按 `student_id` |

### 迁移策略（`migration.py`）

```
启动时读取 JSON
  ├─ 无 version 字段 → 识别为 v1
  │     → 自动迁移为 v2
  │     → 原文件备份为 roll_call_data.v1.bak.json
  │     → 写入新格式文件
  └─ version == 2   → 直接加载
```

迁移步骤：
1. 旧版四个顶层 key 重组为班级对象列表，迁移时班级 `id` 由 `cls_<index>` 生成；新建班级时使用 `uuid.uuid4()` 生成唯一 id
2. `called_students`（完整对象列表）→ `called_ids`（仅 `id` 字符串列表）
3. 每条 record 补充 `"status": "normal"`，`"id"` 字段重命名为 `"student_id"`
4. 每个 student 补充 `"status": "normal"`

迁移仅在首次读取旧文件时执行一次，之后永远读 v2 格式。

---

## 三、核心逻辑

### `logic/roll_call.py` — RollCallEngine

| 方法 | 说明 |
|------|------|
| `get_uncalled()` | 返回未点名学生列表，排除 `absent` / `leave` 状态 |
| `get_called()` | 返回已点名学生列表 |
| `pick_random()` | 从 uncalled 中随机抽一人，返回 Student |
| `mark_called(student_id)` | 将学生 id 加入 called_ids |
| `reset()` | 清空 called_ids，不改变学生状态 |
| `is_complete()` | 所有可点名学生均已点过时返回 True |

**轮询规则：**
- 缺席/请假学生在 `get_uncalled()` 中始终被排除
- `reset()` 只清空 `called_ids`，不影响学生状态
- `is_complete()` 返回 True 时，UI 层负责弹提示并询问是否自动重置

### `logic/statistics.py`

```python
calc_class_stats(records) -> list[dict]
# 返回：[{"student_id": ..., "name": ..., "count": 3, "avg_score": 85.3}]
# 按 student_id 聚合，避免同名学生数据混淆
```

### `data/repository.py` — Repository

| 方法 | 说明 |
|------|------|
| `load()` | 读 JSON，必要时触发 migration |
| `save()` | 原子写：先写 `.tmp`，成功后 rename，防 U 盘断电损坏 |
| `get_data_path()` | 优先 settings 中的路径，否则用 exe 同目录 |
| `set_data_path(path)` | 更新 settings 并保存 |

---

## 四、UI 设计

### 主题

`pyqtdarktheme`（light 模式）+ 少量自定义 QSS 微调字体和间距。纯 QSS 实现，Win7 兼容，无系统 API 依赖。

### 主窗口工具栏

```
[工商管理班 ▼]  [+ 新建班级]  [✎ 重命名]  [🗑 删除班级]     右侧：[⚙ 设置]
```

- 班级切换：QComboBox，切换时刷新所有 Tab 数据
- 删除班级：弹对话框，要求输入班级名称确认后方可删除

### Tab 1：随机点名

布局：左侧 2/3 为点名操作区，右侧 1/3 为已点/未点状态面板。

**点名操作区：**
- 动画显示框（大字体，居中）
- `[随机点名]` `[手动点名]` 按钮
- 评分 QSpinBox（0-100，默认 60）
- `[保存记录]` `[重置轮询]` 按钮

**抽签动画逻辑（仅随机点名触发）：**
1. 点击「随机点名」时，先在内部确定最终抽中的学生
2. QTimer 每 50ms 在动画框随机切换一个学生名字
3. 间隔逐步拉长（50→80→120→200→350ms），模拟缓动
4. 总时长约 2s 后定格在真正抽中的学生
5. 动画期间禁用点名按钮，防止重复触发

**手动点名：** 从学生列表选中后直接显示该学生姓名，不触发动画。

**状态面板（右侧）：**
- 两个 QListWidget：「已点名（N）」「未点名（N）」
- 每次保存记录或重置后实时刷新
- 缺席/请假学生在未点名列表中显示不同颜色标注

### Tab 2：学生管理

- QTableWidget，列：学号 / 姓名 / 状态
- 状态列内嵌 QComboBox，选项：正常 / 缺席 / 请假，切换后实时保存
- 按钮：`[导入 Excel]` `[添加学生]` `[修改]` `[删除]`
- Excel 导入规则：跳过第 1 行表头（字段：学号 / 姓名），学号从整数转为字符串
- 导入时重置 `called_ids`，导入人数限制放宽至 1-200 人（原为 10-100）

### Tab 3：记录查询

- QTableWidget，列：学号 / 姓名 / 时间 / 分数 / 状态
- 统计区按 `student_id` 聚合
- 导出按钮拆为：`[导出本班成绩单]` `[导出全部班级]`
- 全部班级导出：每个班级一个 Sheet，文件名为「全部班级成绩单_YYYY-MM-DD.xlsx」

### Tab 4：统计图表（新增）

- matplotlib `FigureCanvasQTAgg` 嵌入，后端强制 `Agg`
- X 轴：学生姓名，Y 轴：点名次数，柱状图
- 底部文字：平均分 / 最高分 / 最低分
- `[刷新]` 按钮手动刷新图表数据

### 设置对话框

- 数据文件路径输入框 + `[浏览...]` 按钮 + `[恢复默认]` 按钮
- 修改路径后立即生效，下次启动读新路径

---

## 五、Bug 修复清单

| # | 位置 | 问题 | 修复 |
|---|------|------|------|
| B1 | `init_data` L30 | 字典字面量内自引用未定义变量，启动即崩溃 | 先定义班级列表变量再构造 dict |
| B2 | `add_student` L251, `edit_student` L264 | `QLineEdit.getText()` 不存在 | 改为 `QInputDialog.getText()` |
| B3 | `init_student_tab` L222 | `manage_student_list` 从不刷新 | `refresh_student_list()` 同时更新两个列表 |
| B4 | 全局 | 无班级切换机制 | 改为 QComboBox + 切换时刷新所有 Tab |
| B5 | `import_students` L234 | 未跳过表头行，表头被当作学生导入 | `min_row=2` 跳过第 1 行 |
| B6 | `calculate_statistics` L329 | 按姓名聚合，同名学生数据混淆 | 改为按 `student_id` 聚合 |
| B7 | `DATA_PATH` L15 | 相对路径依赖启动目录 | 改为相对 exe 目录的绝对路径 |
| B8 | `import random` L160 | import 写在函数内 | 移至文件顶部 |

---

## 六、打包 & 依赖

### 依赖

```
PyQt5>=5.15
pyqtdarktheme
matplotlib
openpyxl
PyInstaller
```

### 打包命令

```bash
pyinstaller --onefile --windowed --name 随机点名系统 main.py
```

### 关键配置

- `--windowed`：不弹命令行窗口
- `data/` 目录**不打包进 exe**，始终读取 exe 同目录文件，U 盘携带数据
- `assets/` 打包进 exe
- matplotlib 后端强制 `Agg`，避免依赖 Win10+ 渲染 API
- 打包环境建议 Win7 兼容模式，或使用 `--win-private-assemblies`

---

## 七、不在本次范围内

- 网络同步 / 多设备共享
- 用户账号体系
- 打印功能
- 历史版本对比
