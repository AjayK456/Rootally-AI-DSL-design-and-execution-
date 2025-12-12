# src/parser.py
from lark import Lark, Transformer, v_args
from src.ast_nodes import (
    ScriptAST,
    FieldNode,
    NumberNode,
    FunctionNode,
    CompareNode,
    BoolNode,
    CrossNode
)

GRAMMAR = r"""
start: entry_block exit_block?

entry_block: "ENTRY:" expr
exit_block: "EXIT:" expr

?expr: expr "AND" expr   -> and_op
     | expr "OR" expr    -> or_op
     | comparison
     | cross
     | value

comparison: value COMP value
cross: value CROSS_OP value

?value: FIELD                -> field
      | NUMBER               -> number
      | function_call

function_call: NAME "(" [value ("," value)*] ")"

FIELD: /(open|high|low|close|volume)/i
NAME: /(sma|ema|rsi)/i

NUMBER: /[0-9]+(\.[0-9]+)?/

CROSS_OP: /(CROSSES_ABOVE|CROSSES_BELOW)/i
COMP: ">" | "<" | ">=" | "<=" | "==" | "!="

%import common.WS
%ignore WS
"""

parser = Lark(GRAMMAR, start="start", parser="lalr")


# -------------------------------
# TRANSFORMER
# -------------------------------
class ASTBuilder(Transformer):

    def start(self, items):
        entry = items[0]
        exit_ = items[1] if len(items) > 1 else None
        return ScriptAST(entry=entry, exit=exit_)

    def entry_block(self, items):
        return items[0]

    def exit_block(self, items):
        return items[0]

    def and_op(self, items):
        return BoolNode(op="AND", left=items[0], right=items[1])

    def or_op(self, items):
        return BoolNode(op="OR", left=items[0], right=items[1])

    def comparison(self, items):
        left, op, right = items
        return CompareNode(left=left, op=op, right=right)

    def cross(self, items):
        left, op, right = items
        return CrossNode(left=left, op=op, right=right)

    def field(self, items):
        return FieldNode(name=str(items[0]).lower())

    def number(self, items):
        return NumberNode(value=float(items[0]))

    def function_call(self, items):
        name = str(items[0]).lower()
        args = items[1:]
        return FunctionNode(name=name, args=args)

    def COMP(self, token):
        return str(token)

    def CROSS_OP(self, token):
        return str(token)

    def NAME(self, token):
        return str(token)

    def FIELD(self, token):
        return str(token)

    def NUMBER(self, token):
        return str(token)


def parse_dsl(text: str):
    try:
        tree = parser.parse(text)
        ast = ASTBuilder().transform(tree)
        return ast
    except Exception as e:
        print("\n❌ Error while parsing DSL:")
        print(text)
        print("\nUnderlying:", str(e))
        raise
