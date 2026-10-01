"""The built-in procedures required by spec section 5."""

# 本文件实现 spec.md 第 5 节的内置过程：算术、比较、列表操作、类型判断和输出。
# 求值器先把实参算成值，再调用这里的函数；if、quote 等特殊形式由求值器单独处理。
# reduce 把多个值依次合成一个结果；mul 是 Python 提供的两数相乘函数。
from functools import reduce
from operator import mul

# values 模块负责 mini-Scheme 的数据表示、列表遍历和打印格式。
from values import (Closure, Pair, Primitive, Symbol, eq_value, equal_value,
                    is_list, iter_list, make_list, nil, scheme_str)


def _subtract(first, *rest):
    # first 接收第一个数；*rest 把其余实参收集为元组，例如 (4, 1)。
    if not rest:
        # 只有一个实参时取相反数：(- 5) 得到 -5。
        return -first
    # 从 first 开始，按顺序减去 rest 中的数：(- 10 4 1) 即 (10 - 4) - 1。
    # lambda 是一个简短的匿名函数，这里的 a 是累计结果，b 是当前要减去的数。
    return reduce(lambda a, b: a - b, rest, first)


def _trunc_div(a, b):
    if isinstance(a, int) and isinstance(b, int):
        # 两个整数相除，先算绝对值的整数商，再补上正负号，以实现“向零截断”。
        # 例如 -7 / 2 要得到 -3；直接使用 Python 的 -7 // 2 会得到 -4。
        q = abs(a) // abs(b)
        # 两个数一正一负时商为负；(a < 0) != (b < 0) 正是在检查符号是否不同。
        return -q if (a < 0) != (b < 0) else q
    # 至少一个实参不是整数时，沿用 Python 的普通除法。
    return a / b


def _divide(first, *rest):
    if not rest:
        # 单参数 / 求倒数；1.0 确保结果为浮点数，例如 (/ 2) 得到 0.5。
        return 1.0 / first
    # 多参数 / 从左向右依次除：(/ 20 3 2) 先得整数商 6，再得整数商 3。
    return reduce(_trunc_div, rest, first)


def _compare(test, *values):
    # test 是具体的比较函数；同一段链式比较代码可用于 =、<、>、<=、>=。
    if len(values) < 2:
        # 不足两个值时没有任何相邻值需要检查，这份实现返回真。
        return True
    # values[1:] 去掉第一个值；zip 配成相邻项，如 (2, 3, 4) 得到 (2, 3)、(3, 4)。
    for left, right in zip(values, values[1:]):
        if not test(left, right):
            # 任意一对比较失败，整条比较立即为假。
            return False
    # 相邻的每一对都满足条件，才返回真。
    return True


def _car(pair):
    # 点对 Pair 存两项：first 是第一项，rest 是第二项；空表 nil 不是点对。
    if not isinstance(pair, Pair):
        raise TypeError("car expects a pair")
    return pair.first


def _cdr(pair):
    if not isinstance(pair, Pair):
        raise TypeError("cdr expects a pair")
    # 对真列表，第二项是剩余的列表；对 (cons 1 2)，第二项就是数字 2。
    return pair.rest


def _append(*lists):
    # 先收集各个列表里的元素，再用它们创建一条新的点对链。
    items = []
    for value in lists:
        # iter_list 沿 rest 遍历，要求链最终到达 nil；(1 . 2) 这样的点对不是真列表。
        items.extend(iter_list(value))
    # make_list 把 Python 列表转为 mini-Scheme 真列表；没有实参时得到空表。
    return make_list(items)


def _number(value):
    # Python 的 bool 是 int 的子类，因此必须排除 bool，避免把 #t、#f 判为数字。
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _display(value, output):
    # 真正的字符串直接写出，保留实际换行等字符；其他值按 mini-Scheme 格式写出。
    # Symbol 是 str 的子类，故用 type(value) is str 精确区分字符串和符号。
    output.write(value if type(value) is str else scheme_str(value))
    # None 表示“没有求值结果”；main.py 不再打印它，避免多出一行结果。
    return None


def _newline(output):
    # 只往输出流写一个换行，不产生需要在顶层打印的值。
    output.write("\n")
    return None


def install_primitives(env, output):
    # 字典将 mini-Scheme 中的名字映射到 Python 函数，最后统一注册到环境 env。
    # output 是输出流；display 和 newline 的匿名函数会记住它，供调用时使用。
    functions = {
        # 算术：*args 接收任意多个实参；零实参 + 返回 0，零实参 * 返回 1。
        "+": lambda *args: sum(args),
        "-": _subtract,
        "*": lambda *args: reduce(mul, args, 1),
        "/": _divide,
        "modulo": lambda a, b: a % b,
        "quotient": _trunc_div,
        "expt": pow,
        "abs": abs,
        # 比较：*xs 收集实参，再把它们展开传给 _compare，逐对检查。
        "=": lambda *xs: _compare(lambda a, b: a == b, *xs),
        "<": lambda *xs: _compare(lambda a, b: a < b, *xs),
        ">": lambda *xs: _compare(lambda a, b: a > b, *xs),
        "<=": lambda *xs: _compare(lambda a, b: a <= b, *xs),
        ">=": lambda *xs: _compare(lambda a, b: a >= b, *xs),
        # mini-Scheme 只有 #f 为假；is False 避免把 0、空表或空字符串也当成假。
        "not": lambda value: value is False,
        # 列表：cons 直接调用 Pair 构造点对；list 则创建以 nil 结尾的真列表。
        "cons": Pair,
        "car": _car,
        "cdr": _cdr,
        "list": lambda *args: make_list(args),
        # 遍历时每个元素计数 1；同 append 一样，length 的实参必须是真列表。
        "length": lambda value: sum(1 for _ in iter_list(value)),
        "append": _append,
        "null?": lambda value: value is nil,
        "pair?": lambda value: isinstance(value, Pair),
        "list?": is_list,
        # 类型谓词：名字以 ? 结尾表示“是否……”，返回 #t 或 #f。
        "number?": _number,
        "boolean?": lambda value: type(value) is bool,
        "symbol?": lambda value: isinstance(value, Symbol),
        # 精确检查 str，保证 (string? 'x) 为 #f，即使 Symbol 继承了 Python 的 str。
        "string?": lambda value: type(value) is str,
        # 内置过程 Primitive 和用户通过 lambda 创建的 Closure 都是可调用的过程。
        "procedure?": lambda value: isinstance(value, (Primitive, Closure)),
        # 数值谓词：测试是否为零、偶数或奇数；% 是求余运算符。
        "zero?": lambda value: value == 0,
        "even?": lambda value: value % 2 == 0,
        "odd?": lambda value: value % 2 != 0,
        # 相等判断：eq? 对复合数据检查是否同一对象；equal? 逐层比较内容。
        # 两个函数也会区分布尔与数字、符号与字符串，避免 Python 相等规则造成混淆。
        "eq?": eq_value,
        "equal?": equal_value,
        # 输出：在这里绑定 output，让 Scheme 调用 display 时只需要传待显示的值。
        "display": lambda value: _display(value, output),
        "newline": lambda: _newline(output),
    }
    for name, function in functions.items():
        # Symbol(name) 是 Scheme 中可查找的名字；Primitive 包装对应的 Python 函数。
        # env.define 保存这个绑定，所以后续求值 (+ 1 2) 时能查到并调用 +。
        env.define(Symbol(name), Primitive(name, function))
