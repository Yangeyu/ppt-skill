"""页面评论官（DESIGN §12）。

- structural.py  结构评论官：纯 Python 读已测原语（QUALITY §2.1–2.4），可证地板
- aesthetic.py   美学评论官：视觉模型读截图（QUALITY §2.5）
- repair.py      重生成循环编排
"""
from .structural import critique_structure, StructuralIssue
from .aesthetic import critique_aesthetic, critique_deck, AestheticReport

__all__ = ["critique_structure", "StructuralIssue",
           "critique_aesthetic", "critique_deck", "AestheticReport"]
