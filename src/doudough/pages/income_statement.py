import dash_mantine_components as dmc
from dash import dash_table, dcc
from fava.util.date import Interval
from plotly import graph_objects as go

from .app_shell.controls import (
    OPERATING_CURRENCY,
    INTERVAL,
    GraphHelper,
    Output,
    DataHelper,
    filtered_callback,
    get_filtered_ledger,
    Control,
)
from .utils import interval_plot, treeify_accounts, yield_tree_nodes
from ..charting import create_breakdown_chart, create_hierarchy_sankey_data

INCOME_GRAPH = GraphHelper("income_timeline")
GRAPH_TOGGLE = Control("graph_toggle", value="net")
INCOME_TABLE = DataHelper("income_table")
EXPENSES_TABLE = DataHelper("expenses_table")


children = []
for table in [INCOME_TABLE, EXPENSES_TABLE]:
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

grid = dmc.SimpleGrid(cols=2, children=children)

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
                dmc.TabsPanel(dcc.Graph(v["value"] + "_graph"), value=v["value"])
                for v in views
            ],
            dmc.TabsPanel(dcc.Graph("sankey_graph"), value="sankey"),
        ],
        value=views[0]["value"],
    ),
    grid,
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


@filtered_callback(
    *[
        Output("{}_graph".format(f), "figure")
        for f in ["net", "income_time", "expenses_time"]
    ],
    OPERATING_CURRENCY.input,
    INTERVAL.input,
)
def update_chart(currency, interval, fk):

    if not isinstance(interval, Interval):
        interval = Interval(interval)

    ledger, filtered = get_filtered_ledger(**fk)

    root_accounts = ("Income", "Expenses")

    # match graph_type:
    #     case "net":
    #         root_accounts = ("Income", "Expenses")
    #     case "income_time":
    #         root_accounts = "Income"
    #     case "expenses_time":
    #         root_accounts = "Expenses"
    #     case _:
    #         root_accounts = graph_type.capitalize()

    interval_totals = ledger.charts.interval_totals(
        filtered, interval, root_accounts, currency, invert=True
    )

    dates = [it.date for it in interval_totals]
    net = [it.balance.get(currency, 0) for it in interval_totals]
    income = [
        sum(
            [
                i.get(currency, 0)
                for acct, i in it.account_balances.items()
                if acct.startswith("I")
            ]
        )
        for it in interval_totals
    ]
    expenses = [
        sum(
            [
                i.get(currency, 0)
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


@filtered_callback(
    Output("sankey_graph", "figure"),
    Output("income_graph", "figure"),
    Output("expenses_graph", component_property="figure"),
    OPERATING_CURRENCY.input,
)
def update_breakdowns(currency, fk):

    roots = {"Income": {"scale": "Blues"}, "Expenses": {"scale": "Reds"}}
    ledger, filtered = get_filtered_ledger(**fk)

    data = {
        root: ledger.charts.hierarchy(filtered, root, currency) for root in roots.keys()
    }

    node, link = create_hierarchy_sankey_data(
        data["Income"], data["Expenses"], currency, max_hierarchy=3
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
        create_breakdown_chart(data[root], currency, **props)
        for root, props in roots.items()
    ]

    return sankey, *tuple(figs)


@filtered_callback(INCOME_TABLE.output, OPERATING_CURRENCY.input)
def update_income_table(currency, fk):
    return _update_table(currency, "Income", invert=-1, **fk)


@filtered_callback(EXPENSES_TABLE.output, OPERATING_CURRENCY.input)
def update_expenses_table(currency, fk):
    return _update_table(currency, "Expenses", invert=-1, **fk)


def _update_table(currency, account_root, invert=1, **fk):
    data = get_hierarchy_data(currency, account_root, **fk)

    data = [
        {"account": treeify_accounts(d["account"]), "total": invert * d["total"]}
        for d in data
    ]

    return data


def get_hierarchy_data(currency, account_root, **fk):
    ledger, filtered = get_filtered_ledger(**fk)
    hierarchy = ledger.charts.hierarchy(
        filtered, account_root, currency
    )  # need this directly for sankey
    data = [
        {
            "account": node.account,
            "total": node.balance_children.get(currency, 0),
        }
        for node in yield_tree_nodes(hierarchy)
    ]

    return data
