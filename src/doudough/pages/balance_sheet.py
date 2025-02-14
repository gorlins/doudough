from datetime import date

import dash_mantine_components as dmc
import pandas as pd
from dash import dcc, Output
from fava.util.date import Interval
from plotly import express as px, graph_objects as go

from .app_shell.controls import (
    DataHelper,
    filtered_ledger_callback,
    INTERVAL,
)
from .income_statement import _update_table, make_table
from ..charting import create_breakdown_chart, create_hierarchy_sankey_data

ASSETS_TABLE = DataHelper("assets_table")
LIABILITIES_TABLE = DataHelper("liabilities_table")


views = [
    {"value": "net", "label": "Net Worth"},
    {"value": "assets", "label": "Assets", "invert": 1, "scale": "Blues"},
    {"value": "liabilities", "label": "Liabilities", "invert": -1, "scale": "Reds"},
    {"value": "equity", "label": "Equity", "scale": "Purples", "invert": -1},
]

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
                    dcc.Graph(
                        "balance_{}_graph".format(v["value"]),
                    ),
                    value=v["value"],
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
    dmc.SimpleGrid(
        cols=2,
        children=[make_table(table.id) for table in [ASSETS_TABLE, LIABILITIES_TABLE]],
    ),
]


@filtered_ledger_callback(
    Output("balance_sankey_graph", "figure"),
    *[Output("balance_{}_graph".format(v["value"]), "figure") for v in views[1:]],
    ASSETS_TABLE.output,
    LIABILITIES_TABLE.output,
)
def update_breakdowns(context):
    roots = {
        "Assets": {"scale": "Blues"},
        "Liabilities": {"scale": "Reds"},
        "Equity": {"scale": "Purples"},
    }

    data = {
        root: context.ledger.charts.hierarchy(
            context.filtered, root, context.operating_currency
        )
        for root in roots.keys()
    }

    node, link = create_hierarchy_sankey_data(
        data["Assets"],
        data["Liabilities"],
        context.operating_currency,
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
        root: create_breakdown_chart(data[root], context.operating_currency, **props)
        for root, props in roots.items()
    }

    return (
        sankey,
        figs["Assets"],
        figs["Liabilities"],
        figs["Equity"],
        _update_table(context, "Assets"),
        _update_table(context, "Liabilities"),
    )


@filtered_ledger_callback(Output("balance_net_graph", "figure"), INTERVAL.input)
def update_nw_chart(context, interval):

    interval = Interval.get(interval)

    nw = context.ledger.charts.net_worth(
        context.filtered, interval, context.operating_currency
    )

    today = date.today()
    fig = px.area(
        pd.DataFrame(
            [
                (
                    it.date,
                    it.balance.get(context.operating_currency, 0),
                    it.date < today,
                )
                for it in nw
            ],
            columns=["date", "net_worth", "future"],
        ),
        # fillgradient={"type": "vertical"},
        x="date",
        y="net_worth",
    )
    fig.update_layout(xaxis_title=None, yaxis_title=None)

    return fig
