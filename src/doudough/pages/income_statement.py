import dash_mantine_components as dmc
from dash import dash_table, dcc
from fava.util.date import Interval
from plotly import graph_objects as go

from .app_shell.controls import (
    GraphHelper,
    Output,
    DataHelper,
    filtered_ledger_callback,
    Control,
    INTERVAL,
)
from .utils import interval_plot, treeify_accounts, yield_tree_nodes
from ..charting import create_breakdown_chart, create_hierarchy_sankey_data

INCOME_GRAPH = GraphHelper("income_timeline")
GRAPH_TOGGLE = Control("graph_toggle", value="net")
INCOME_TABLE = DataHelper("income_table")
EXPENSES_TABLE = DataHelper("expenses_table")


def make_table(id):
    return dash_table.DataTable(
        id=id,
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
        style_cell_conditional=[{"if": {"column_id": "account"}, "textAlign": "left"}],
        style_as_list_view=True,
    )


views = [
    {"value": "net", "label": "Net Profit"},
    {"value": "income_time", "label": "Income (time)"},
    {"value": "expenses_time", "label": "Expenses (time)"},
    {"value": "income", "label": "Income"},
    {"value": "expenses", "label": "Expenses"},
]
layout = [
    dmc.Tabs(
        children=[
            dmc.TabsList(
                justify="center",
                children=[
                    dmc.TabsTab(children=v["label"], value=v["value"]) for v in views
                ]
                + [dmc.TabsTab(children="Sankey", value="sankey")],
            ),
            *[
                dmc.TabsPanel(
                    dcc.Graph(v["value"] + "_graph"),
                    value=v["value"],
                )
                for v in views
            ],
            dmc.TabsPanel(dcc.Graph("sankey_graph"), value="sankey"),
        ],
        value=views[0]["value"],
    ),
    dmc.SimpleGrid(
        cols=2,
        children=[make_table(table.id) for table in [INCOME_TABLE, EXPENSES_TABLE]],
    ),
]


# @callback(GRAPH_TOGGLE.make_output("data"), INTERVAL.input)
# def update_graph_toggle(interval):
#     if not isinstance(interval, Interval):
#         interval = Interval(interval)
#     return (
#         [
#             {"value": "net", "label": "Net Profit"},
#             {"value": "income_time", "label": "Income ({})".format(interval.label)},
#             {"value": "expenses_time", "label": "Expenses ({})".format(interval.label)},
#             {"value": "income", "label": "Income"},
#             {"value": "expenses", "label": "Expenses"},
#         ],
#     )


@filtered_ledger_callback(
    *[
        Output("{}_graph".format(f), "figure")
        for f in ["net", "income_time", "expenses_time"]
    ],
    INTERVAL.input,
)
def update_chart(context, interval):

    root_accounts = ("Income", "Expenses")

    interval = Interval.get(interval)

    # match graph_type:
    #     case "net":
    #         root_accounts = ("Income", "Expenses")
    #     case "income_time":
    #         root_accounts = "Income"
    #     case "expenses_time":
    #         root_accounts = "Expenses"
    #     case _:
    #         root_accounts = graph_type.capitalize()

    interval_totals = context.ledger.charts.interval_totals(
        context.filtered,
        interval,
        root_accounts,
        context.operating_currency,
        invert=True,
    )

    dates = [it.date for it in interval_totals]
    net = [it.balance.get(context.operating_currency, 0) for it in interval_totals]
    income = [
        sum(
            [
                i.get(context.operating_currency, 0)
                for acct, i in it.account_balances.items()
                if acct.startswith("I")
            ]
        )
        for it in interval_totals
    ]
    expenses = [
        sum(
            [
                i.get(context.operating_currency, 0)
                for acct, i in it.account_balances.items()
                if acct.startswith("Ex")
            ]
        )
        for it in interval_totals
    ]

    return tuple(
        [
            interval_plot(dates, data, interval=interval)
            for data in [net, income, expenses]
        ]
    )


@filtered_ledger_callback(
    Output("sankey_graph", "figure"),
    Output("income_graph", "figure"),
    Output("expenses_graph", component_property="figure"),
    INCOME_TABLE.output,
    EXPENSES_TABLE.output,
)
def update_breakdowns(context):

    roots = {"Income": {"scale": "Blues"}, "Expenses": {"scale": "Reds"}}

    data = {
        root: context.ledger.charts.hierarchy(
            context.filtered, root, context.operating_currency
        )
        for root in roots.keys()
    }

    node, link = create_hierarchy_sankey_data(
        data["Income"], data["Expenses"], context.operating_currency, max_hierarchy=3
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
    figs = [
        create_breakdown_chart(data[root], context.operating_currency, **props)
        for root, props in roots.items()
    ]

    return (
        sankey,
        *tuple(figs),
        _update_table(context, "Income", invert=-1),
        _update_table(context, "Expenses", invert=-1),
    )


def _update_table(context, account_root, invert=1):
    data = get_hierarchy_data(context, account_root)

    data = [
        {"account": treeify_accounts(d["account"]), "total": invert * d["total"]}
        for d in data
    ]

    return data


def get_hierarchy_data(context, account_root):

    hierarchy = context.ledger.charts.hierarchy(
        context.filtered, account_root, context.operating_currency
    )  # need this directly for sankey
    data = [
        {
            "account": node.account,
            "total": node.balance_children.get(context.operating_currency, 0),
        }
        for node in yield_tree_nodes(hierarchy)
    ]

    return data
