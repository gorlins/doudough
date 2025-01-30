from pprint import pformat

import dash_mantine_components as dmc
from dash import callback

from .app_shell.controls import (
    ChildrenHelper,
    get_ledger,
    LEDGER_SLUG,
)

ERRORS = ChildrenHelper("ledger_errors")


layout = dmc.Code(id=ERRORS.id, block=True)


@callback(ERRORS.output, LEDGER_SLUG.input)
def update_options(slug):
    if slug:
        ledger = get_ledger(slug)
        return pformat(ledger.errors)
    return "Not Loaded"
