"""Base app class."""
class BaseApp:
    NAME = "App"
    ICON = "?"
    WIDTH = 720
    HEIGHT = 460

    def launch(self, wm):
        return wm.open(self.NAME, self.build, w=self.WIDTH, h=self.HEIGHT, icon=self.ICON)

    def build(self, parent):
        raise NotImplementedError