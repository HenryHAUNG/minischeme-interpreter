"""Variable bindings with lexical parent scopes."""


class Environment:
    def __init__(self, parent=None):
        # 每层环境都有自己的绑定表；parent 指向外层环境，顶层的 parent 为 None。
        self.parent = parent
        self.values = {}

    def define(self, name, value):
        # define 只写入当前层；同名局部变量会遮住外层变量。
        self.values[name] = value

    def lookup(self, name):
        # 先查当前层，找不到再向外查；这条链由函数定义处的环境决定。
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        # 已经查到最外层仍没有这个名字，说明使用了未定义的变量或函数。
        raise NameError(f"undefined symbol: {name}")
