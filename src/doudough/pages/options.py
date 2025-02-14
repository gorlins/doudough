from pprint import pformat

import dash_mantine_components as dmc

from .app_shell.controls import (
    ledger_layout,
)


#
# FOPTS_MAP = ChildrenHelper("fava_options_map_display")
# OPTIONS_MAP = ChildrenHelper("options_map_display")


@ledger_layout
def layout(ledger, **kwargs):
    return [
        "Fava options",
        dmc.Code(block=True, children=pformat(ledger.fava_options)),
        "Beancount options",
        dmc.Code(block=True, children=pformat(ledger.options)),
    ]


# @callback(FOPTS_MAP.output, OPTIONS_MAP.output, BFILE.input)
# def update_options(bfile):
#     if bfile:
#         ledger = get_ledger(bfile)
#         return pformat(ledger.fava_options), pformat(ledger.options)
#     return "Not Loaded", "Not Loaded"
