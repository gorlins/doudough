from pprint import pformat

import dash_mantine_components as dmc

from .app_shell.controls import (
    ledger_layout,
)


# ERRORS = ChildrenHelper("ledger_errors")


# layout = dmc.Code(id=ERRORS.id, block=True)


@ledger_layout
def layout(ledger, **kwargs):
    if ledger:
        return dmc.Code(pformat(ledger.errors), block=True)


#
# @callback(ERRORS.output, BFILE.input)
# def update_options(bfile):
#     if bfile:
#         ledger = get_ledger(bfile)
#         # if ledger.errors:
#         #     b = dmc.Badge(str(len(ledger.errors)), color="red", variant="filled")
#         # else:
#         #     b = dmc.Badge("✓", color="green", variant="light")
#         return pformat(ledger.errors)
#     # db = dmc.Badge("?", color="grey", variant="outline")
#     return "Not Loaded"
