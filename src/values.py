"""Runtime values and Scheme formatting."""

from dataclasses import dataclass


class Symbol(str):
    """A Scheme name, distinct from a Scheme string."""
    # 同样写成 x，符号代表待查找的名字，字符串 "x" 则是文本值。


class Nil:
    # Scheme 的空表单独用一种类型表示，不与 Python 的空列表或 None 混用。
    def __repr__(self):
        return "()"


# 全程序共用这一个空表对象，可以用 is nil 判断链是否到达空表结尾。
nil = Nil()


@dataclass(eq=False)
class Pair:
    # 点对由两个部分组成；真列表是一串 Pair，其最后一个 rest 为 nil。
    # eq=False 禁止自动生成按字段比较的相等方法，同一性由 eq_value 判断。
    first: object
    rest: object


@dataclass(eq=False)
class Closure:
    # 闭包保存形参、函数体和定义时的环境；调用时才计算函数体。
    params: tuple
    body: tuple
    env: object


@dataclass(eq=False)
class Primitive:
    # 把 Python 函数包装成 Scheme 的内置过程，统一交给求值器调用。
    name: str
    func: object

    def __call__(self, args):
        # args 是已经求值的实参列表，*args 将其展开为 Python 函数的参数。
        return self.func(*args)


def make_list(items, tail=nil):
    # 从后往前接点对，例如 [1, 2] → Pair(1, Pair(2, nil))。
    # 自定义 tail 可构造非空表结尾的点对，例如 items=[1]、tail=2 表示 (1 . 2)。
    for item in reversed(items):
        tail = Pair(item, tail)
    return tail


def iter_list(value):
    # 沿 rest 遍历并依次交出 first，供 length、append 等函数使用。
    while isinstance(value, Pair):
        yield value.first
        value = value.rest
    if value is not nil:
        # 遍历后尾部不是空表，例如 (1 . 2)，说明它不是一个真列表。
        raise TypeError("expected a proper list")


def is_list(value):
    # 空表也是真列表；沿整条链检查最后是否以 nil 结束。
    while isinstance(value, Pair):
        value = value.rest
    return value is nil


def equal_value(left, right):
    # equal? 比内容与结构：用待比较栈代替逐项递归，避免长列表耗尽 Python 调用栈。
    pending = [(left, right)]
    while pending:
        left, right = pending.pop()
        if isinstance(left, Pair) or isinstance(right, Pair):
            if not (isinstance(left, Pair) and isinstance(right, Pair)):
                return False
            # 两边都是点对时，其首项和尾部也必须相等，嵌套列表同样适用。
            pending.append((left.rest, right.rest))
            pending.append((left.first, right.first))
        elif left is nil or right is nil:
            if left is not right:
                return False
        elif isinstance(left, bool) or isinstance(right, bool):
            # Python 中 True == 1，但 Scheme 的布尔值不能与数字视为相等。
            if type(left) is not type(right) or not (left == right):
                return False
        elif isinstance(left, Symbol) or isinstance(right, Symbol):
            # Symbol 继承 str，所以要先区分符号 'a 与字符串 "a" 的类型。
            if type(left) is not type(right) or not (left == right):
                return False
        elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
            # 两边确实是数字时按数值比较，因此 1 与 1.0 相等。
            if not (left == right):
                return False
        elif type(left) is not type(right) or not (left == right):
            return False
    return True


def eq_value(left, right):
    # eq? 对数字、布尔、符号按值比较；对点对等其他对象检查是否为同一个对象。
    if left is nil or right is nil:
        return left is right
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, Symbol) or isinstance(right, Symbol):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return left is right


def scheme_str(value):
    # 将运行结果转换为题目要求的文本，不能直接照搬 Python 的 repr 输出。
    if value is nil:
        return "()"
    if isinstance(value, bool):
        # 布尔值要输出为 #t/#f，不能直接输出 Python 的 True/False。
        return "#t" if value else "#f"
    if isinstance(value, Symbol):
        # 符号不加引号；必须在普通字符串之前判断，因为 Symbol 是 str 的子类。
        return str(value)
    if isinstance(value, str):
        # 顶层字符串输出带双引号，将特殊字符重新写成转义形式。
        escaped = (value.replace("\\", "\\\\").replace('"', '\\"')
                   .replace("\n", "\\n").replace("\t", "\\t"))
        return '"' + escaped + '"'
    if isinstance(value, Pair):
        # 沿点对链收集各项；尾部是 nil 时打印为列表，否则保留点号和尾部。
        items = []
        current = value
        while isinstance(current, Pair):
            items.append(scheme_str(current.first))
            current = current.rest
        if current is nil:
            return "(" + " ".join(items) + ")"
        return "(" + " ".join(items) + " . " + scheme_str(current) + ")"
    if isinstance(value, (Closure, Primitive)):
        # 函数值统一显示成过程标记，不展示 Python 对象内部信息。
        return "#<procedure>"
    return str(value)
