from plotly import express as px


class CHART_TYPES:

    class BREAKDOWN:
        icycle = px.icicle
        sunburst = px.sunburst


def create_breakdown_chart(
    data, graph_type="icycle", invert=1, scale="Blues", min_fraction=0.05, **kwargs
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

    lookup = {d["account"]: invert * d["total"] for d in data}
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
