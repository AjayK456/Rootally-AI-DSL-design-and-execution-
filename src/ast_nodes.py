# src/ast_nodes.py
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class ASTNode:
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

@dataclass
class FieldNode(ASTNode):
    name: str
    def to_dict(self):
        return {"type": "field", "name": self.name}

@dataclass
class NumberNode(ASTNode):
    value: float
    def to_dict(self):
        return {"type": "number", "value": self.value}

@dataclass
class FunctionNode(ASTNode):
    name: str
    args: list
    def to_dict(self):
        return {"type": "function", "name": self.name.lower(), "args": [a.to_dict() if isinstance(a, ASTNode) else a for a in self.args]}

@dataclass
class CompareNode(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode
    def to_dict(self):
        return {"type": "compare", "left": self.left.to_dict(), "op": self.op, "right": self.right.to_dict()}

@dataclass
class BoolNode(ASTNode):
    op: str  # "AND" or "OR"
    left: ASTNode
    right: ASTNode
    def to_dict(self):
        return {"type": "bool", "op": self.op, "left": self.left.to_dict(), "right": self.right.to_dict()}

@dataclass
class CrossNode(ASTNode):
    dir: str  # "CROSSES_ABOVE" or "CROSSES_BELOW"
    left: ASTNode
    right: ASTNode
    def to_dict(self):
        return {"type": "cross", "dir": self.dir.lower(), "left": self.left.to_dict(), "right": self.right.to_dict()}

@dataclass
class ScriptAST:
    entry: Optional[ASTNode] = None
    exit: Optional[ASTNode] = None
    def to_dict(self):
        return {"entry": self.entry.to_dict() if self.entry else None,
                "exit": self.exit.to_dict() if self.exit else None}
