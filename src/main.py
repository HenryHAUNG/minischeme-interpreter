"""Run mini-Scheme programs from files or standard input."""

import sys
from pathlib import Path

from environment import Environment
from evaluator import evaluate
from primitives import install_primitives
from reader import read_all
from values import scheme_str


# 解释器的整体流程：源码文本 → 读取表达式 → 求值 → 按 Scheme 格式输出。
# env 是变量和函数的绑定表；output 是接收输出的对象，通常为标准输出。
def run(source, env, output):
    # 一个文件可以写多个顶层表达式，按出现顺序逐个执行。
    for expression in read_all(source):
        result = evaluate(expression, env)
        # display/newline 等表达式返回 None：它们已经自行输出，不能再打印结果。
        if result is not None:
            output.write(scheme_str(result) + "\n")


def main(argv=None):
    if argv is None:
        # 命令行第一个元素是本脚本的路径，后面的元素才是待执行的文件路径。
        argv = sys.argv[1:]
    # 启动时创建全局环境，并登记 +、car、display 等内置函数。
    env = Environment()
    install_primitives(env, sys.stdout)
    if argv:
        for path in argv:
            # 所有文件共用同一个 env，因此后一个文件能使用前一个文件定义的名字。
            run(Path(path).read_text(encoding="utf-8"), env, sys.stdout)
    else:
        # 不传文件路径时，从标准输入读取，支持管道输入或手动输入。
        run(sys.stdin.read(), env, sys.stdout)


if __name__ == "__main__":
    # 直接运行本文件时启动；被其他 Python 文件导入时不自动执行。
    main()
