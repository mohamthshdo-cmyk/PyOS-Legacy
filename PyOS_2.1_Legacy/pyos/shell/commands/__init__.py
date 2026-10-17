"""Central command registry."""
from pyos.shell.commands import fs, sys, apps, text, env, jobs_cmds
try:
    from pyos.shell.commands import help as help_mod
except Exception:
    help_mod = None

ALL_COMMANDS = {}
ALL_BY_CATEGORY = {}

for module in (fs, sys, apps, text, env, jobs_cmds):
    for name, entry in module.COMMANDS.items():
        fn, desc, category = entry
        ALL_COMMANDS[name] = (fn, desc, category)
        ALL_BY_CATEGORY.setdefault(category, []).append((name, desc))

if help_mod is not None:
    for name, entry in help_mod.COMMANDS.items():
        fn, desc, category = entry
        ALL_COMMANDS[name] = (fn, desc, category)
        ALL_BY_CATEGORY.setdefault(category, []).append((name, desc))
