"""Evaluate expressions using lexical environments."""

from environment import Environment
from reader import DottedList
from values import Closure, Primitive, Symbol, make_list, nil


# 求值器把 reader 读出的表达式变成结果；环境 env 保存名字与值的对应关系。
# Python 的 list 在这里表示待解释的语法；Scheme 运行时列表则用 Pair 点对链表示。
def quote_data(expr):
    # quote 里的内容是数据，不应查变量或调用函数，只转换列表的存储形式。
    if isinstance(expr, list):
        # 逐层转换嵌套列表；make_list 会把元素接成以空表 nil 结尾的点对链。
        return make_list([quote_data(item) for item in expr])
    if isinstance(expr, DottedList):
        # 点列表 '(1 2 . 3) 的尾部是 3；也要转换尾部，不能一律补上空表。
        return make_list([quote_data(item) for item in expr.items], quote_data(expr.tail))
    # 数字、布尔、字符串、符号等基本数据直接保留，包括尚未定义的符号。
    return expr


def evaluate_sequence(body, env):
    # begin、函数体、let 和 cond 的子句共用这条规则：依次执行，返回最后一个值。
    # 空的表达式序列没有结果，用 None 表示；入口程序遇到 None 不打印结果行。
    result = None
    for expression in body:
        result = evaluate(expression, env)
    return result


def apply(proc, args):
    # args 已经是求值后的参数值，不是原始的语法表达式。
    if isinstance(proc, Primitive):
        # 内置过程由 Python 函数实现，Primitive 会将参数列表展开后交给该函数。
        return proc(args)
    if isinstance(proc, Closure):
        # 本语言的用户函数只支持固定参数个数。
        if len(args) != len(proc.params):
            raise TypeError("wrong number of arguments")
        # 新建本次调用的局部环境，父环境取函数定义时保存的 proc.env。
        # 这就是词法作用域：外部名字从定义处查找，而不是从调用处查找。
        local = Environment(proc.env)
        for name, value in zip(proc.params, args):
            # 将形参名与实参值一一绑定；每次调用都有自己的局部变量。
            local.define(name, value)
        return evaluate_sequence(proc.body, local)
    # 例如 (1 + 2) 会尝试调用数字 1，所以走到这里报错。
    raise TypeError(f"not a procedure: {proc!r}")


def evaluate(expr, env):
    if isinstance(expr, Symbol):
        # 单独的符号表示变量引用：在当前环境及其父环境中查找对应的值。
        return env.lookup(expr)
    if isinstance(expr, DottedList):
        # 点列表只能作为 quote 的数据，不能直接当作可执行表达式。
        raise SyntaxError("dotted list is only valid as quoted data")
    if not isinstance(expr, list):
        # 数字、字符串、布尔等基本值不需要计算，结果就是它们自身。
        return expr
    if not expr:
        # 直接写 () 会被视为缺少操作符的调用；写 '() 才会得到空表数据。
        raise SyntaxError("empty expression cannot be called")

    # 将括号表达式拆成第一项 head 和其余各项 rest；特殊形式由第一项的名字识别。
    head, *rest = expr
    form = str(head) if isinstance(head, Symbol) else None
    if form == "quote":
        # 不调用 evaluate 处理参数，所以 'x 返回符号 x，本身不要求 x 已被定义。
        return quote_data(rest[0])
    if form == "if":
        condition = evaluate(rest[0], env)
        # Scheme 中只有 #f（Python 的 False）是假，0、空表和空字符串都是真。
        # 因此用 is not False 判断，不能直接套用 Python 的真假规则。
        if condition is not False:
            # 只求值被选中的分支；另一个分支即使会出错也不会执行。
            return evaluate(rest[1], env)
        # 假分支可以省略，此时条件为假便返回 None。
        return evaluate(rest[2], env) if len(rest) > 2 else None
    if form == "cond":
        # 依次检查各子句，遇到第一个为真的测试便停止；else 无条件匹配。
        for clause in rest:
            test, *body = clause
            test_value = True if isinstance(test, Symbol) and test == "else" else evaluate(test, env)
            if test_value is not False:
                # 匹配后顺序执行子句中的表达式；没有表达式则返回测试值自身。
                return evaluate_sequence(body, env) if body else test_value
        # 所有子句都不匹配时没有结果。
        return None
    if form == "and":
        # and 从左到右求值，遇到 #f 立刻返回，不执行后续表达式（短路）。
        # 初始值 True 也规定了没有参数的 (and) 返回 #t。
        result = True
        for operand in rest:
            result = evaluate(operand, env)
            if result is False:
                return False
        # 全部通过时返回最后一个值，该值未必是布尔值。
        return result
    if form == "or":
        # or 遇到第一个非 #f 的值就直接返回它，后续表达式不会执行。
        for operand in rest:
            result = evaluate(operand, env)
            if result is not False:
                return result
        # 全为假或没有参数的 (or) 都返回 #f。
        return False
    if form == "define":
        target = rest[0]
        if isinstance(target, list):
            # (define (square x) (* x x)) 是定义函数的简写，函数体现在不执行。
            name, *params = target
            value = Closure(tuple(params), tuple(rest[1:]), env)
        else:
            # (define x 表达式) 先计算右侧，再把结果绑定到名字 x。
            name = target
            value = evaluate(rest[1], env)
        # 闭包保存的是 env 这个环境对象；绑定函数名后，函数体也能找到自身来递归。
        env.define(name, value)
        # define 的结果是刚定义的符号名，入口程序会把它单独打印一行。
        return name
    if form == "lambda":
        # 保存参数、函数体和定义时的环境，生成闭包；等到 apply 调用它才执行函数体。
        return Closure(tuple(rest[0]), tuple(rest[1:]), env)
    if form == "let":
        bindings, *body = rest
        # 先在同一个外层 env 中计算所有右侧，再加入新环境，这叫“并行绑定”。
        # “并行”不是同时运行：此处仍按顺序计算，但本轮新绑定互不可见。
        prepared = [(name, evaluate(value, env)) for name, value in bindings]
        local = Environment(env)
        for name, value in prepared:
            local.define(name, value)
        # let 的局部名字只在新环境及其内部可见，函数体返回最后一个表达式的值。
        return evaluate_sequence(body, local)
    if form == "begin":
        # begin 顺序执行，并沿用当前环境，所以其中的 define 对该环境生效。
        return evaluate_sequence(rest, env)

    # 其余括号表达式按普通函数调用处理：先求值操作符，再从左到右求值全部实参。
    # 操作符也可以是表达式，如 ((lambda (x) (* x 2)) 5)。
    procedure = evaluate(head, env)
    arguments = [evaluate(arg, env) for arg in rest]
    # 所有实参都求值完成后，才把结果交给内置过程或用户闭包。
    return apply(procedure, arguments)
