from datetime import date

import dash_mantine_components as dmc
import pandas as pd
from dash import dash_table, dcc, Output
from fava.util.date import Interval
from plotly import express as px, graph_objects as go

from .app_shell.controls import (
    OPERATING_CURRENCY,
    DataHelper,
    INTERVAL,
    get_filtered_ledger,
    filtered_callback,
)
from .income_statement import _update_table
from ..charting import create_breakdown_chart, create_hierarchy_sankey_data

ASSETS_TABLE = DataHelper("assets_table")
LIABILITIES_TABLE = DataHelper("liabilities_table")


children = []
for table in [ASSETS_TABLE, LIABILITIES_TABLE]:

    children.append(
        dash_table.DataTable(
            id=table.id,
            columns=[
                dict(id="account", name="Account"),
                dict(
                    id="total",
                    name="Total",
                    type="numeric",
                    format=dash_table.FormatTemplate.money(2),
                ),
            ],
            style_cell={"fontSize": "smaller"},
            style_cell_conditional=[
                {"if": {"column_id": "account"}, "textAlign": "left"}
            ],
            style_as_list_view=True,
        )
    )
views = [
    {"value": "net", "label": "Net Worth"},
    {"value": "assets", "label": "Assets", "invert": 1, "scale": "Blues"},
    {"value": "liabilities", "label": "Liabilities", "invert": -1, "scale": "Reds"},
    {"value": "equity", "label": "Equity", "scale": "Purples", "invert": -1},
]
grid = dmc.SimpleGrid(cols=2, children=children)
layout = [
    dmc.Tabs(
        children=[
            dmc.TabsList(
                justify="center",
                children=[
                    dmc.TabsTab(children=v["label"], value=v["value"]) for v in views
                ]
                + [dmc.TabsTab("Sankey", value="balance_sankey")],
            ),
            *[
                dmc.TabsPanel(
                    dcc.Graph("balance_{}_graph".format(v["value"])), value=v["value"]
                )
                for v in views
            ]
            + [
                dmc.TabsPanel(
                    dcc.Graph(
                        "balance_sankey_graph",
                    ),
                    value="balance_sankey",
                )
            ],
        ],
        value=views[0]["value"],
    ),
    grid,
]


@filtered_callback(
    Output("balance_sankey_graph", "figure"),
    *[Output("balance_{}_graph".format(v["value"]), "figure") for v in views[1:]],
    OPERATING_CURRENCY.input,
)
def update_breakdowns(currency, fk):

    # return tuple(
    #     [
    #         create_breakdown_chart(
    #             get_hierarchy_data(currency, v["value"].capitalize(), **fk),
    #             scale=v["scale"],
    #             invert=v["invert"],
    #         )
    #         for v in views[1:]
    #     ]
    # )

    roots = {
        "Assets": {"scale": "Blues"},
        "Liabilities": {"scale": "Reds"},
        "Equity": {"scale": "Purples"},
    }
    ledger, filtered = get_filtered_ledger(**fk)

    data = {
        root: ledger.charts.hierarchy(filtered, root, currency) for root in roots.keys()
    }

    node, link = create_hierarchy_sankey_data(
        data["Assets"],
        data["Liabilities"],
        currency,
        max_hierarchy=3,
        net_labels=("NET_WORTH", "NET_DEBT"),
    )

    node["align"] = "left"
    sankey = go.Figure(
        go.Sankey(
            # arrangement="snap"
            # arrangement="perpendicular",
            node=node,
            link=link,
        )
    )
    figs = {
        root: create_breakdown_chart(data[root], currency, **props)
        for root, props in roots.items()
    }

    return sankey, figs["Assets"], figs["Liabilities"], figs["Equity"]


@filtered_callback(
    Output("balance_net_graph", "figure"),
    OPERATING_CURRENCY.input,
    INTERVAL.input,
)
def update_nw_chart(currency, interval, fk):

    if not isinstance(interval, Interval):
        interval = Interval(interval)

    ledger, filtered = get_filtered_ledger(**fk)
    nw = ledger.charts.net_worth(filtered, interval, "at_value")

    today = date.today()
    fig = px.area(
        pd.DataFrame(
            [(it.date, it.balance.get(currency, 0), it.date < today) for it in nw],
            columns=["date", "net_worth", "future"],
        ),
        # fillgradient={"type": "vertical"},
        x="date",
        y="net_worth",
    )
    fig.update_layout(xaxis_title=None, yaxis_title=None)

    return fig


@filtered_callback(ASSETS_TABLE.output, OPERATING_CURRENCY.input)
def update_assets_table(currency, fk):
    return _update_table(currency, "Assets", **fk)


@filtered_callback(
    LIABILITIES_TABLE.output,
    OPERATING_CURRENCY.input,
)
def update_liabilities_table(currency, fk):
    return _update_table(currency, "Liabilities", **fk)
