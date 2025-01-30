from typing import List

import dash_ag_grid as dag
import dash_mantine_components as dmc
from beancount.core import data as D
from beancount.core.convert import get_weight
from dash import Output, callback, Input, Patch, State
from fava.beans.funcs import hash_entry
from fava.core.file import get_entry_slice

from .app_shell.controls import (
    DataHelper,
    filtered_callback,
    get_filtered_ledger,
    get_ledger,
    LEDGER_SLUG,
)

JOURNAL_TABLE = DataHelper("journal")


FILTER_BUTTONS = [
    {"id": "open"},
    {"id": "close"},
    {"id": "transaction"},
    {"id": "*"},
    {"id": "!"},
    {"id": "x"},
    {"id": "balance"},
    {"id": "note"},
    {"id": "doc"},
    {"id": "d"},
    {"id": "l"},
    {"id": "pad"},
    {"id": "query"},
    {"id": "custom"},
    {"id": "b"},
]
FLAGS = ["!", "x", "*"]

COLUMN_DEFS = [
    {
        "field": "date",
        "cellDataType": "dateString",
        # "checkboxSelection": True,
        # "headerCheckboxSelection": True,
        # 'colSpan': {"function": "params.data.country === 'Russia' ? 2 : 1"}
        # "tooltipField": "raw",
    },
    {"field": "type", "filterParams": {"maxNumConditions": 10}},
    {
        "field": "f",
        "filterParams": {
            "maxNumConditions": 10,
        },
    },
    {"field": "payee"},
    {"field": "narration"},
    # {"field": "weight"},
    # {"field": "pop", "headerName": "Population"},
    # {"field": "lifeExp", "headerName": "Life Expectancy"},
    {
        "field": "value",
        "type": "numericColumn",
        "pinned": "right",
        "valueFormatter": {"function": "d3.format('($,.2f')(params.value)"},
    },
]
code = dmc.Code(block=True)
modal = dmc.Modal(
    title="Source View",
    id="modal-simple",
    children=[
        code,
        # dmc.Space(h=20),
        # dmc.Group(
        #     [
        #         # dmc.Button("Close", id="modal-close-button"),
        #         # dmc.Button(
        #         #     "Close",
        #         #     color="red",
        #         #     variant="outline",
        #         #     id="modal-close-button",
        #         # ),
        #     ],
        #     justify="flex-end",
        # ),
    ],
)
grid = dag.AgGrid(
    id="ledger",
    rowData=[],
    columnDefs=COLUMN_DEFS,
    defaultColDef={
        "editable": True,
        "filter": True,
        # "floatingFilter": True,
        # "checkboxSelection": {
        #     "function": "params.column == params.columnApi.getAllDisplayedColumns()[0]"
        # },
        # "headerCheckboxSelection": {
        #     "function": "params.column == params.columnApi.getAllDisplayedColumns()[0]"
        # },
    },
    # columnSize="responsiveSizeToFit",
    getRowId="params.data.id",
    columnSize="autoSize",
    columnSizeOptions={"skipHeader": False},
    dashGridOptions={
        "pagination": True,
        "rowSelection": "single",
        "skipHeaderOnAutoSize": True,
        # "enableBrowserTooltips": True,
        # "suppressRowClickSelection": True,
    },
)

layout = [
    dmc.Group(
        [
            modal,
            dmc.ChipGroup(
                [
                    dmc.Chip(
                        value=f["id"],
                        children=f.get("f", f["id"]).capitalize(),
                        size="xs",
                        radius="xs",
                    )
                    for f in FILTER_BUTTONS
                ],
                value=[f["id"] for f in FILTER_BUTTONS],
                multiple=True,
                id="filter_chips",
            ),
            dmc.TextInput(id="journal_qf", placeholder="filter..."),
        ],
        justify="flex-end",
        gap="xs",
    ),
    grid,
]


@callback(
    Output(modal, "opened"),
    Output(code, "children"),
    Input(grid, "selectedRows"),
    State(LEDGER_SLUG.id, "value"),
    State(modal, "opened"),
    prevent_initial_call=True,
)
def view_source(selection, ledger_slug, is_open):

    if not selection:
        return False, ""

    if is_open:
        return False, ""

    ledger = get_ledger(ledger_slug)
    entry = ledger.get_entry(selection[0]["id"])
    source, sha = get_entry_slice(entry)
    return True, source


@callback(Output(grid, "dashGridOptions"), Input("journal_qf", "value"))
def quickfilter(filter_value):
    newFilter = Patch()
    newFilter["quickFilterText"] = filter_value
    return newFilter


@callback(Output(grid, "filterModel"), Input("filter_chips", "value"))
def filter_types(values):
    f = Patch()
    f["type"] = {
        "filterType": "text",
        "operator": "OR",
        "conditions": [
            {"filterType": "text", "type": "equals", "filter": t.capitalize()}
            for t in values
            if t not in FLAGS
        ],
    }
    f["f"] = {  # TODO: implement x
        "filterType": "text",
        "operator": "OR",
        "conditions": [
            {"filterType": "text", "type": "equals", "filter": f}
            for f in values
            if f in FLAGS
        ],
    }
    return f


# @callback(Output("graph-content", "figure"), Input("dropdown-selection", "value"))
# def update_graph(value):
#     dff = df[df.country == value]
#     return px.line(dff, x="year", y="pop")


def to_datagrid(transactions: List[D.Directive]) -> List[dict]:
    return list(map(_to_datagrid, transactions))


def _to_datagrid(t: D.Directive) -> dict:

    typ = type(t)
    r = {"id": hash_entry(t), "date": t.date, "type": typ.__name__}

    match typ:
        case D.Transaction:
            r.update(
                {
                    "f": t.flag,
                    "payee": t.payee,
                    "narration": t.narration,
                    "value": sum([abs(get_weight(p).number) for p in t.postings]) / 2,
                }
            )
        case _:
            r["f"] = typ.__name__

    # with StringIO() as s:
    #     print_entry(t, file=s)
    #     row = {
    #
    #         "account": t.postings[1].account,
    #         "increase": (
    #             t.postings[0].units.number
    #             if t.postings[0].units.number >= 0
    #             else None
    #         ),
    #         "decrease": (
    #             -1 * t.postings[0].units.number
    #             if t.postings[0].units.number < 0
    #             else None
    #         ),
    #         "currency": t.postings[0].units.currency,
    #         "raw": s.getvalue(),
    #     }

    return r


# @callback(
#     Output("entry-display", "children"),
#     Input("ledger", "selectedRows"),
# )
# def select_entry(selected_rows):
#     return selected_rows[0]["raw"]
#
#     # beanquery
#     txs = [e for e in entries if isinstance(e, Transaction)]
#
#     all_accounts = defaultdict(set)
#     for t in txs:
#         for p in t.postings:
#             all_accounts[p.account.split(":", 1)[0]].add(p.account)
#
#     grid = d


@filtered_callback(Output(grid, "rowData"))
def update_journal(**fk):
    print(fk)
    ledger, filtered = get_filtered_ledger(**fk)
    return to_datagrid(filtered.entries)
