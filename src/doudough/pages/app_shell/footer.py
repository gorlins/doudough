import dash_mantine_components as dmc
from dash import callback, dcc
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
from fava.application import _slug

from .controls import (
    LOADED,
    LEDGER_SLUG,
    get_loader,
    UPDATE_INTERVAL,
)
from .header import SIZE

layout = dmc.AppShellFooter(
    dmc.Group(
        [
            UPDATE_INTERVAL.make_widget(dcc.Interval),
            LOADED.make_widget(dmc.Badge, variant="dot"),
            LEDGER_SLUG.make_widget(
                dmc.Select,
                size=SIZE,
                placeholder="Ledger File",
                clearable=False,
                # disabled=True,
                leftSection=DashIconify(icon="material-symbols:edit-document"),
            ),
        ],
        justify="flex-end",
        h="100%",
        px="md",
        align="center",
    ),
)


@callback(
    LEDGER_SLUG.output,
    LEDGER_SLUG.make_output("data"),
    LEDGER_SLUG.input,
    UPDATE_INTERVAL.input,
)
def update_slugs(current_slug, interval):

    loader = get_loader()
    if current_slug in loader.ledgers_by_slug:
        raise PreventUpdate()
    else:
        new_slug = loader.first_slug()

    return new_slug, [_slug(ledger) for ledger in loader.ledgers]
