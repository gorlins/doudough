from pprint import pformat

import dash_mantine_components as dmc
from dash import callback

from .app_shell.controls import (
    ChildrenHelper,
    get_ledger,
    BFILE,
)

ERRORS = ChildrenHelper("ledger_errors")


layout = dmc.Code(id=ERRORS.id, block=True)


@callback(ERRORS.output, BFILE.input)
def update_options(bfile):
    if bfile:
        ledger = get_ledger(bfile)
        # if ledger.errors:
        #     b = dmc.Badge(str(len(ledger.errors)), color="red", variant="filled")
        # else:
        #     b = dmc.Badge("✓", color="green", variant="light")
        return pformat(ledger.errors)
    # db = dmc.Badge("?", color="grey", variant="outline")
    return "Not Loaded"
