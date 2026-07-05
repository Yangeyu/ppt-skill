"""艺术总监 / 身份生成层（DESIGN §4）。

- director.py        给定主题 → 现场生成一份 SpecLock（LLM 或确定性兜底）
- identity_critic.py 校验生成的设计语言体系是否成立（QUALITY §1，纯 Python）
"""
from .identity_critic import critique_identity, IdentityIssue
from .director import art_direct, DesignBrief

__all__ = ["critique_identity", "IdentityIssue", "art_direct", "DesignBrief"]
