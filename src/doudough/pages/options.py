from pprint import pformat

import dash_mantine_components as dmc
from dash import callback

from .app_shell.controls import (
    ChildrenHelper,
    get_ledger,
    BFILE,
)

FOPTS_MAP = ChildrenHelper("fava_options_map_display")
OPTIONS_MAP = ChildrenHelper("options_map_display")


layout = [
    "Fava options",
    dmc.Code(id=FOPTS_MAP.id, block=True),
    "Beancount options",
    dmc.Code(id=OPTIONS_MAP.id, block=True),
]


@callback(FOPTS_MAP.output, OPTIONS_MAP.output, BFILE.input)
def update_options(bfile):
    if bfile:
        ledger = get_ledger(bfile)
        return pformat(ledger.fava_options), pformat(ledger.options)
    return "Not Loaded", "Not Loaded"
