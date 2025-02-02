from collections import defaultdict
from dataclasses import dataclass
from typing import List

import networkx as nx
from beancount.core.convert import get_weight
from beancount.core.data import Transaction
from fava.core.tree import SerialisedTreeNode
from plotly import express as px, graph_objects as go

from .pages.utils import yield_tree_nodes


class CHART_TYPES:

    class BREAKDOWN:
        icycle = px.icicle
        sunburst = px.sunburst


@dataclass
class BreakdownParams:
    invert: int = 1
    direction: int = 1

    @classmethod
    def from_account(cls, account: str):

        invert = 1
        direction = 1
        match account.split(":", 1)[0]:
            case "Income":
                invert = -1
                pass
            case "Expenses":
                direction = -1
            case "Assets":
                pass
            case "Liabilities":
                invert = -1
                direction = -1
            case "Equity":
                invert = -1
                direction = 1
            case _:
                raise ValueError(account)

        return cls(invert=invert, direction=direction)


def create_breakdown_chart(
    node: SerialisedTreeNode,
    currency,
    graph_type="icycle",
    scale="Blues",
    min_fraction=0.05,
    **kwargs,
):
    """Create a hierarchical breakdown chart (icycle, sunburst, etc)

    Note that this chart type is only accurate if all rendered breakdown values are positive and all rollups are
    greater or equal to the sum of their rendered components.  That is, Expenses = 100, Expenses:Shopping = 110,
    Expenses:Taxes:Refund = -10 cannot be accurately rendered without 'inflating' the Expenses to 110, which is
    inaccurate.  To prevent some of these issues without changing the rollups, set min_fraction to hide small groups
    to provide enough flexibility in the display to swallow up the negative numbers.

    :param data: produced by ledger.get_hierarchy_data
    :param int invert: 1 or -1, to swap the sign (e.g. for Income accounts).
    :param float min_fraction: hide breakdowns below this amount of the total rollup.  This prevents displaying
    negative numbers, and also prevents visible clutter from many small breakouts, as well as providing a bit
    more flexibility when there are small negative accounts that prevent fully accurate visualizations
    """

    bp = BreakdownParams.from_account(node.account)

    lookup = {
        n.account: bp.invert * n.balance_children.get(currency, 0)
        for n in yield_tree_nodes(node)
    }

    sd = []
    mx = max(lookup.values())
    assert mx > 0
    min_display = min_fraction * float(
        mx
    )  # Annoying issue multiplying float and Decimal
    pruned = []

    for account, value in lookup.items():
        if any(account.startswith(p) for p in pruned):
            # This branch is pruned - do not include any children
            continue
        if value < min_display:
            # Ignore negative nodes and hide really small ones too
            pruned.append(account)
            continue
        splits = account.split(":")
        parent = ":".join(splits[:-1])

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

    if isinstance(graph_type, str):
        graph_type = getattr(CHART_TYPES.BREAKDOWN, graph_type)

    fig = graph_type(
        sd,
        names="name",
        ids="id",
        parents="parent",
        values="value",
        branchvalues="total",
        color="value",
        range_color=(0, mx),
        color_continuous_scale=scale,
        **kwargs,
    )

    return fig


def truncate_account(acct: str, maxdepth: int):
    return ":".join(acct.split(":")[:maxdepth])


def _to_hierarchy_links(
    root_node: SerialisedTreeNode, currency, max_hierarchy=2
) -> list:

    bp = BreakdownParams.from_account(root_node.account)

    links = []

    total = bp.invert * root_node.balance_children.get(currency, 0)
    assert total >= 0
    mn = total / 20
    for node in yield_tree_nodes(root_node):
        splits = node.account.split(":")

        if len(splits) > max_hierarchy:
            continue
        if len(splits) == 1:
            continue
        parent = ":".join(splits[:-1])
        balance = bp.invert * node.balance_children.get(currency, 0)
        if balance < mn:
            continue

        if bp.direction == 1:
            links.append((node.account, parent, balance))
        else:
            links.append((parent, node.account, balance))

    return links


def create_hierarchy_sankey_data(
    left: SerialisedTreeNode,
    right: SerialisedTreeNode,
    currency,
    net_labels=("PROFIT", "LOSS"),
    max_hierarchy=2,
):

    links = _to_hierarchy_links(
        left, currency, max_hierarchy=max_hierarchy
    ) + _to_hierarchy_links(right, currency, max_hierarchy=max_hierarchy)

    # Need an approximate sorting of nodes
    # label = []
    # inflows = defaultdict(lambda: 0)
    # outflows = defaultdict(lambda: 0)
    # for s, t, v in links:
    #     for n in (s, t):
    #         if n not in inflows and n not in outflows:
    #             # Have not yet seen this node
    #             label.append(n)
    #
    #     outflows[s] += v
    #     inflows[t] += v

    # node_relatives = [
    #     ((inflows[n] - outflows[n]) / max(0.0001, abs(by_acct[n])), n)
    #     for n in found_nodes
    # ]
    # label = [n[1] for n in sorted(node_relatives)]
    tin = BreakdownParams.from_account(left.account).invert * left.balance_children.get(
        currency, 0
    )
    tout = BreakdownParams.from_account(
        right.account
    ).invert * right.balance_children.get(currency, 0)

    net_positive, net_negative = net_labels

    if tin > tout:
        links.append((left.account, net_positive, tin - tout))
        # label.append(net_positive)
    else:
        links.append((net_negative, right.account, tout - tin))
        # label.insert(0, net_negative)

    links.append((left.account, right.account, min(tin, tout)))

    source, target, value = zip(*links)

    # The default layout doesn't work super well in plotly
    # Results are better if we sort the nodes first with a good
    # digraph algorithm
    dag = nx.DiGraph([l[:2] for l in links])
    # pos = nx.multipartite_layout(dag)
    label = list(nx.topological_sort(dag))

    # pos = nx.drawing.spring_layout(dag)
    # pos = nx.drawing.arf_layout(dag)
    # pos = nx.drawing.forceatlas2_layout(dag)
    # label = [l[1] for l in sorted([(v[1], k) for k, v in pos.items()])]

    idx = {l: i for i, l in enumerate(label)}
    node = {
        "label": [l.split(":")[-1] for l in label],
        "align": "left",
    }
    link = {
        "source": [idx[s] for s in source],
        "target": [idx[t] for t in target],
        "value": value,
    }
    return node, link


def to_sankey_data(txns: List[Transaction], maxdepth=2):

    linktotals = defaultdict(lambda: 0)
    inflows = defaultdict(lambda: 0)
    outflows = defaultdict(lambda: 0)

    for txn in txns:
        if not isinstance(txn, Transaction):
            continue

        if len(txn.postings) == 2:
            if txn.postings[0].units.number < 0:
                source = txn.postings[0]
                dest = txn.postings[1]
            else:
                source = txn.postings[1]
                dest = txn.postings[0]

            sa = truncate_account(source.account, maxdepth)
            da = truncate_account(dest.account, maxdepth)

            if sa == da:
                continue
            weight = get_weight(dest).number
            # links.append((source.account, dest.account, dest.amount))
            outflows[sa] += weight
            inflows[da] += weight

            linktotals[(sa, da)] += weight

        else:
            # todo: implement???
            pass

    abstotals = defaultdict(lambda: 0)

    for (sa, da), weight in linktotals.items():
        if sa < da:
            abstotals[(sa, da)] += weight
        else:
            abstotals[(da, sa)] -= weight

    # Sort in approximate topological order
    relative_flow = lambda a: (inflows[a] - outflows[a]) / (inflows[a] + outflows[a])
    nodes = sorted(
        set([l[0] for l in abstotals.keys()]).union(
            set([l[1] for l in abstotals.keys()])
        ),
        key=relative_flow,
    )
    nindex = {a: i for i, a in enumerate(nodes)}

    account_type = [truncate_account(a, 1) for a in nodes]
    atypes = sorted(set(account_type))
    atind = {a: i for i, a in enumerate(atypes)}

    source = []
    target = []
    value = []
    for (s, t), v in abstotals.items():
        if v < 0:
            t, s = s, t
            v *= -1
        source.append(nindex[s])
        target.append(nindex[t])
        value.append(v)

    node = dict(
        label=nodes,
        # Doesn't seem to work if there are any size 1 groups?
        # groups=[[atind[a] for a in account_type]]
        # x=[
        #     0.5 + 0.5 * float((inflows[n] - outflows[n]) / (inflows[n] + outflows[n]))
        #     for n in nodes
        # ],
        # y=[i / len(nodes) for i in range(len(nodes))],
    )
    link = dict(
        source=source,
        target=target,
        value=list(map(float, value)),
    )

    return node, link


def create_sankey_chart(txs: List[Transaction], maxdepth=2, **sankey_opts):
    node, link = to_sankey_data(txs, maxdepth=maxdepth)

    return go.Figure(
        go.Sankey(
            # arrangement="snap"
            # arrangement="perpendicular",
            node=node,
            link=link,
            **sankey_opts,
        )
    )
