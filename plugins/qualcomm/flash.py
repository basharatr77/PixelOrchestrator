from core.plugins.base import BasePlugin
class QualcommPlugin(BasePlugin):
    @property
    def name(self): return "qualcomm"
    def register(self, registry): registry.register_operation("qcom.flash", lambda **kw: {"status":"ok"})
plugin = QualcommPlugin()
