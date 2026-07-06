"""评论官 —— 五重机器关卡里的四个零模型评论官(第五关 = pydantic schema 本身)。

- identity.py    身份评论官:look 包 SpecLock 的作者门禁(字阶/配色/对比/字体配对)
- structural.py  结构评论官:读浏览器已测原语,抓越界/重叠/离板色/低对比
- facts.py       事实评论官:数字溯源/闭合槽位/结构数量,抓幻觉与推导
- density.py     密度评论官:页面信息量下限,档位声明在各 look 包 LOOK.density

美学(视觉模型读图)不在引擎内——引擎零模型,视觉评审属于外部 agent
(如 mastra visionCritic 读 cli --render 的 LibreOffice 真渲染)。"""
from .identity import critique_identity, IdentityIssue, identity_ok
from .structural import critique_structure, StructuralIssue
from .facts import check_facts
from .density import check_density, density_profile

__all__ = ["critique_identity", "IdentityIssue", "identity_ok",
           "critique_structure", "StructuralIssue",
           "check_facts", "check_density", "density_profile"]
