from time import time
from typing import List

import dash_ag_grid as dag
import dash_mantine_components as dmc
from beancount.core import data as D
from dash import callback, Input
from dash.dash_table import DataTable
from beancount.core.convert import get_weight
from beancount.core.data import Transaction
from dash.dash_table import DataTable
from fava.beans.funcs import hash_entry
from fava.core.group_entries import TransactionPosting
from fava.core.tree import SerialisedTreeNode

from .app_shell.controls import Output, filtered_ledger_callback, Context

# layout = dmc.Accordion(id="expenses_payees", children=[], multiple=True)
tree = dmc.Tree(
    id="expenses_payees",
    data=[{"value": "asdf", "label": "<LOADING>", "children": []}],
    selectOnClick=True,
)

COLUMN_DEFS = [
    {
        "field": "date",
        "cellDataType": "dateString",
        # "checkboxSelection": True,
        # "headerCheckboxSelection": True,
        # 'colSpan': {"function": "params.data.country === 'Russia' ? 2 : 1"}
        # "tooltipField": "raw",
    },
    {"field": "payee"},
    {"field": "narration"},
    {"field": "account"},
    {
        "field": "value",
        "type": "numericColumn",
        "pinned": "right",
        "valueFormatter": {"function": "d3.format('($,.2f')(params.value)"},
    },
]


# table = dag.AgGrid(
#     id="payee_ledger",
#     rowData=[],
#     columnDefs=COLUMN_DEFS,
#     defaultColDef={
#         # "editable": True,
#         "filter": True,
#         # "floatingFilter": True,
#         # "checkboxSelection": {
#         #     "function": "params.column == params.columnApi.getAllDisplayedColumns()[0]"
#         # },
#         # "headerCheckboxSelection": {
#         #     "function": "params.column == params.columnApi.getAllDisplayedColumns()[0]"
#         # },
#     },
#     columnSize="responsiveSizeToFit",
#     getRowId="params.data.id",
#     # columnSize="autoSize",
#     columnSizeOptions={"skipHeader": False},
#     dashGridOptions={
#         "pagination": True,
#         # "rowSelection": "single",
#         "skipHeaderOnAutoSize": True,
#         # "enableBrowserTooltips": True,
#         # "suppressRowClickSelection": True,
#     },
# )
table = DataTable(
    id="payee_ledger",
    columns=[{"name": c["field"], "id": c["field"]} for c in COLUMN_DEFS],
    filter_action="native",
    sort_action="native",
    page_size=100,
)
layout = dmc.Grid(children=[dmc.GridCol(tree, span=3), dmc.GridCol(table, span=9)])


class MyTree:
    def __init__(self, value):

        self.v = value
        self.children = {}
        self.transactions = []

    @property
    def label(self):
        return self.v.split(":")[-1]

    def add_tp(self, tp: TransactionPosting):
        key = tp.posting.account + ":" + (tp.transaction.payee or "-NONE-")
        parts = key.split(":")

        node = self
        for i, part in enumerate(parts):
            if part == self.v:
                continue  # don't get stuck adding 'Expenses' in a loop
            if not part in node.children:
                node.children[part] = self.__class__(":".join(parts[: i + 1]))
            node = node.children[part]

        node.transactions.append(tp)

    def to_accordian_item(self):
        return dmc.AccordionItem(
            [
                dmc.AccordionControl(self.label),
                dmc.AccordionPanel(
                    [t.to_accordian_item() for n, t in sorted(self.children.items())]
                    + (
                        [
                            dmc.Table(
                                data={
                                    "head": ["date", "narration", "amount"],
                                    "body": [
                                        [
                                            t.transaction.date,
                                            t.transaction.narration,
                                            str(t.posting.units),
                                        ]
                                        for t in self.transactions
                                    ],
                                }
                            )
                        ]
                        if False  # self.transactions
                        else []
                    )
                ),
            ],
            value=self.v,
        )


def to_tree_node(node: SerialisedTreeNode, currency, results) -> dict:

    my_payees = [r[1] or "-NONE-" for r in results if r[0] == node.account]
    child_results = [r for r in results if r[0].startswith(node.account + ":")]

    return {
        "value": node.account,
        "label": node.account.split(":")[-1],
        "children": [
            to_tree_node(child, currency, child_results) for child in node.children
        ]
        + [{"value": (node.account, payee), "label": payee} for payee in my_payees],
    }


@filtered_ledger_callback(Output("expenses_payees", "data"))
def update_tree(context: Context):
    t0 = time()
    rtypes, results = context.filtered_query(
        "select account, payee where account ~ 'Income|Expenses' group by account, payee order by account, payee"
    )
    t1 = time()
    hier = [
        to_tree_node(
            context.ledger.charts.hierarchy(
                context.filtered, root, context.operating_currency
            ),
            context.operating_currency,
            results,
        )
        for root in ["Income", "Expenses"]
    ]

    print("query:", t1 - t0)
    print("hierarchy:", time() - t1)
    return hier


# @filtered_ledger_callback(Output("expenses_payees", "children"))
# def update_ep(context):
#     expense_accounts = defaultdict(lambda: defaultdict(list))
#
#     tree = MyTree("Expenses")
#
#     for trans in context.filtered.entries:
#         if isinstance(trans, Transaction):
#             for p in trans.postings:
#                 if p.account.startswith("Expenses:"):
#                     tree.add_tp(TransactionPosting(trans, p))
#
#     return [t.to_accordian_item() for n, t in sorted(tree.children.items())]


def to_datagrid(transactions: List[D.Directive]) -> List[dict]:
    out = []

    t0 = time()
    for t in transactions:
        if not isinstance(t, Transaction):
            continue
        tr = {
            # "tid": hash_entry(t),
            "date": t.date,
            "payee": t.payee or "",
            "narration": t.narration,
        }
        for p in t.postings:

            out.append(dict(account=p.account, value=get_weight(p).number, **tr))
    print("dg:", time() - t0)
    return out


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


@filtered_ledger_callback(Output(table, "data"))
def update_journal(context):
    return to_datagrid(context.filtered.entries)


@callback(Output(table, "filter_query"), Input(tree, "selected"))
def apply_filter(selected):
    if not selected:
        return ""
    assert len(selected) == 1
    s = selected[0]
    if isinstance(s, str):
        fq = " ".join(["{account}", "scontains", s])
    else:
        account, payee = s
        if payee == "-NONE-":
            payee = ""
        fq = " ".join(
            [
                "{account}",
                "scontains",
                account,
                "&&",
                "{payee}",
                "eq",
                '"{}"'.format(payee),
            ]
        )

    print(fq)
    return fq
