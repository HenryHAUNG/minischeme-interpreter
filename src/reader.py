"""Convert source text into nested expressions."""

import re
from dataclasses import dataclass

from values import Symbol


# token 是从源码中切出的一个词，例如左括号、整数文本或字符串内容。
# frozen=True 表示创建后不再修改，避免解析时意外改变原始 token。
@dataclass(frozen=True)
class Token:
    kind: str
    text: str


@dataclass(frozen=True)
class DottedList:
    # 保存点对语法，例如 (1 2 . 3)：items=(1, 2)，tail=3。
    # 这是解析阶段的表示；quote 求值时才会把它转换为运行时的 Pair 链。
    items: tuple
    tail: object


# 先识别整数和小数，其余普通词按符号处理；单独的 +、- 仍是函数名。
INTEGER = re.compile(r"[+-]?\d+\Z")
FLOAT = re.compile(r"[+-]?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?\Z")


def tokenize(source):
    # 词法分析只切分文本，不执行 Scheme 运算。
    tokens = []
    i = 0
    while i < len(source):
        char = source[i]
        if char.isspace():
            i += 1
        elif char == ";":
            # 分号开始的注释到行尾结束。字符串内的分号由下面的字符串分支处理。
            end = source.find("\n", i)
            i = len(source) if end < 0 else end + 1
        elif char in "()'":
            # 括号和引用简写各自成为一个 token。
            tokens.append(Token(char, char))
            i += 1
        elif char == '"':
            # 进入字符串后一直读到配对双引号，内部空白和分号都属于字符串。
            i += 1
            chars = []
            while i < len(source) and source[i] != '"':
                if source[i] == "\\":
                    # 反斜杠引入转义：例如源码中的 \n 变为字符串中的实际换行。
                    i += 1
                    if i >= len(source):
                        raise SyntaxError("unfinished string escape")
                    chars.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(source[i], source[i]))
                else:
                    chars.append(source[i])
                i += 1
            if i >= len(source):
                raise SyntaxError("unterminated string")
            tokens.append(Token("string", "".join(chars)))
            i += 1
        else:
            # 普通词在空白、括号、分号或引号前结束，例如 define、x、42。
            start = i
            while i < len(source) and not source[i].isspace() and source[i] not in "();'\"":
                i += 1
            tokens.append(Token("atom", source[start:i]))
    return tokens


def atom(token):
    # 将一个基本 token 转为对应的 Python 对象，保留“符号”和“字符串”的区别。
    if token.kind == "string":
        return token.text
    text = token.text
    if text == "#t":
        return True
    if text == "#f":
        return False
    if INTEGER.fullmatch(text):
        return int(text)
    if FLOAT.fullmatch(text):
        return float(text)
    # Symbol 是名字：求值时需要查环境；普通字符串则直接作为值返回。
    return Symbol(text)


def read_all(source):
    # 语法分析把 token 组成嵌套表达式，例如 (+ 1 (* 2 3)) 变成嵌套 Python 列表。
    tokens = tokenize(source)
    position = 0

    def read_one():
        # 递归读取一个表达式；所有递归调用共享位置，读取后继续向前推进。
        nonlocal position
        if position >= len(tokens):
            raise SyntaxError("unexpected end of input")
        token = tokens[position]
        position += 1
        if token.kind == "'":
            # 'x 与 (quote x) 使用同一种内部表示，求值器只需处理 quote。
            return [Symbol("quote"), read_one()]
        if token.kind == "(":
            # 遇到左括号开始收集元素，直到匹配的右括号；嵌套括号由递归处理。
            items = []
            while position < len(tokens) and tokens[position].kind != ")":
                if tokens[position].kind == "atom" and tokens[position].text == ".":
                    # 点号后的一个表达式是尾部；其后必须立即闭合当前括号。
                    position += 1
                    tail = read_one()
                    if position >= len(tokens) or tokens[position].kind != ")":
                        raise SyntaxError("dotted list must end after its tail")
                    position += 1
                    return DottedList(tuple(items), tail)
                items.append(read_one())
            if position >= len(tokens):
                raise SyntaxError("missing closing parenthesis")
            position += 1
            return items
        if token.kind == ")":
            raise SyntaxError("unexpected closing parenthesis")
        return atom(token)

    # 读取全部顶层表达式；空输入或只有注释时返回空列表。
    result = []
    while position < len(tokens):
        result.append(read_one())
    return result
