"""PyOS kernel - boots the OS."""
import datetime
from pyos.kernel.state import STATE
from pyos.kernel import __version__, CODENAME


class Kernel:
    def __init__(self):
        self.running = False

    def boot(self):
        STATE.data["boot_count"] = STATE.data.get("boot_count", 0) + 1
        STATE.boot_time = datetime.datetime.now()
        STATE.log(str(STATE.boot_time) + " boot #" + str(STATE.data["boot_count"]))
        print("PyOS " + __version__ + " (" + CODENAME + ") booting...")
        STATE.save()

        from pyos.system.boot import BootSequence
        self.running = True
        BootSequence().start()
        STATE.save()