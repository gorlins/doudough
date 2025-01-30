import dash_mantine_components as dmc
from dash import dash_table, dcc
from fava.util.date import Interval
from plotly import express as px

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
                ],
            ),
            *[
                dmc.TabsPanel(dcc.Graph(v["value"] + "_graph"), value=v["value"])
                for v in views
            ],
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
    Output("income_graph", "figure"),
    Output("expenses_graph", component_property="figure"),
    OPERATING_CURRENCY.input,
)
def update_breakdowns(currency, fk):

    return tuple(
        [create_breakdown_chart(t, currency, **fk) for t in ["income", "expenses"]]
    )


def create_breakdown_chart(graph_type, currency, **fk):

    good = "Blues"
    bad = "Reds"
    invert = 1
    match graph_type:
        case "assets":
            scale = good
        case "liabilities":
            scale = bad
            invert = -1
        case "income":
            invert = -1
            scale = good
        case "expenses":
            scale = bad
        case "equity":
            scale = "Purples"
            invert = -1
        case _:
            raise ValueError()

    root_account = graph_type.capitalize()
    data = get_hierarchy_data(currency, root_account, **fk)
    lookup = {d["account"]: invert * d["total"] for d in data}
    sd = []

    mx = max(lookup.values())
    assert mx > 0
    min_display = mx / 50
    pruned = []

    for account, value in lookup.items():
        if any(account.startswith(p) for p in pruned):
            # This branch is pruned - do not include any children
            continue
        if value < min_display:
            # Ignore negative nodes and hide really small ones too
            # print("Below min:", account, value)
            pruned.append(account)
            continue
        splits = account.split(":")
        parent = ":".join(splits[:-1])
        # if len(splits) > 3:
        #     print(account, value)
        if parent and value < lookup[parent] / 10:
            pruned.append(account)
            continue

        sd.append(
            {
                "parent": parent,
                "id": account,
                "name": splits[-1],
                "value": float(value),
            }
        )
    fig = px.icicle(
        sd,
        names="name",
        ids="id",
        parents="parent",
        values="value",
        branchvalues="total",
        color="value",
        range_color=(0, mx),
        # color_continuous_midpoint=0,
        color_continuous_scale=scale,
    )

    return fig


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
    hierarchy = ledger.charts.hierarchy(filtered, account_root, currency)
    data = [
        {
            "account": node.account,
            "total": node.balance_children.get(currency, 0),
        }
        for node in yield_tree_nodes(hierarchy)
    ]

    return data
