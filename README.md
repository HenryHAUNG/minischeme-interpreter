# mini-Scheme 解释器

用 Python 3 实现的 mini-Scheme 解释器。六个源码模块附有中文注释，适合沿着“读取 → 求值 → 输出”的流程阅读。程序只使用 Python 3 标准库，无需安装第三方依赖。

## 功能

- 读取整数、布尔、符号、字符串、注释、引用简写和点列表。
- 实现 `quote`、`if`、`cond`、`and`、`or`、`define`、`lambda`、`let`、`begin`。
- 支持词法作用域、闭包、固定参数函数与递归；`and` / `or` 按规则短路求值。
- 提供算术、链式比较、列表操作、类型与相等性谓词、`display` 和 `newline`。
- 从标准输入或一个、多个 `.scm` 文件读取程序；多个文件共用全局环境。
- 按 Scheme 格式输出每个顶层表达式的结果；无值结果不额外打印。

其中只有 `#f` 为假；`0`、空表和空字符串都为真。`let` 的各绑定表达式先在外层环境求值，随后建立局部绑定。解释器实现的是题目规定的子集，不包含宏、可变参数 `lambda` 或尾调用优化保证。

## 目录分工

| 文件 | 作用 |
| --- | --- |
| `src/main.py` | 命令行入口，读取输入并组织求值与输出。 |
| `src/reader.py` | 切分词元，解析表达式、字符串、引用和点列表。 |
| `src/values.py` | 定义符号、点对、空表和过程，并格式化输出。 |
| `src/environment.py` | 保存变量绑定，沿父环境查找名字。 |
| `src/evaluator.py` | 实现特殊形式、闭包和普通过程调用。 |
| `src/primitives.py` | 实现并注册内置过程。 |
| `tests/test_spec_edges.py` | 10 组补充边界测试。 |
| `程序讲解.md` | 阅读顺序、逐步运行示例与关键实现说明。 |

## 运行

在本仓库根目录执行；以下命令中的 `python` 应指向 Python 3。

从标准输入运行：

```text
echo "(+ 1 2)" | python src/main.py
```

输出：

```text
3
```

运行自行编写的 Scheme 文件：

```text
python src/main.py your-program.scm
python src/main.py first.scm second.scm
```

运行仓库内的补充测试：

```text
python -m unittest discover -s tests -v
```

## 核验与题目来源

当前实现已通过原题自测器的 12 组测试，以及本仓库的 10 组补充边界测试。补充测试覆盖短路与真值、词法作用域、`let` 并行绑定、相等性与类型、长列表、负数整数商、跨文件环境和引用点列表等规则。正式评分还有未公开用例，通过这些自测不代表所有输入都已验证。

题目提供的官方公开 starter：[woo114515/minischeme-starter](https://github.com/woo114515/minischeme-starter)。本仓库只收录实现程序、补充测试和程序说明，未收录题目提供的 `autograder.pyz`。如需复现原题的 12 组自测，请从 starter 获取该文件，并在本仓库根目录执行：

```text
python autograder.pyz python src/main.py
```

## AI 参与范围

Codex 在阅读题目规范后辅助完成了模块划分、代码实现、错误定位、中文注释和补充测试编写。运行结果由原题自测器与补充测试核验；阅读者可结合源码和 `程序讲解.md` 了解实现与测试范围。
