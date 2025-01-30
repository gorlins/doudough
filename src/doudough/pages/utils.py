import os
from collections import defaultdict
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from time import time

import dash
import pandas as pd
from beancount.core.data import D
from dash import dash_table
from fava.core.tree import SerialisedTreeNode
from fava.util.date import Interval
from plotly import graph_objects as go


@contextmanager
def timeit(prompt="Time"):
    t0 = time()
    yield
    print(prompt + ":", time() - t0)


def yield_tree_nodes(node: SerialisedTreeNode):
    """Iterate through tree nodes in depth-first topological order"""
    yield node
    for child in node.children:
        yield from yield_tree_nodes(child)


def register(name=None, path=None, **kwargs):

    def wrapper(func, name=name, path=path):
        name = name or func.__doc__.split("\n", 1)[0]
        path = path or "/" + func.__name__
        module = func.__module__
        if module == "__main__":
            module = os.path.basename(__file__)  # because it's in this file
        dash.register_page(module, layout=func, name=name, path=path, **kwargs)
        return func

    return wrapper


def table_from_df(df: pd.DataFrame, **kwargs) -> dash_table.DataTable:
    # Convert all decimals
    df = df.reset_index()
    df = df.astype(
        {col: float for col, val in df.iloc[0].items() if isinstance(val, Decimal)}
    )
    return dash_table.DataTable(
        data=df.to_dict(orient="records"),
        # style_cell={"textAlign": "left"},
        style_cell_conditional=[
            {"if": {"column_id": c}, "textAlign": "left"}
            for c, dt in df.dtypes.items()
            if dt.hasobject
        ]
        + [
            # {
            #     "if": {"filter_query": "{{'{}'}} < 0".format(c)},
            #     "column_id": c,
            #     "color": "red",
            # }
            # for c, dt in df.dtypes.items()
            # if dt.kind == "f"
        ],
        # columns=[CONTEXT.format_column(col)]
        # [{"name": i, "id": i} for i in df.columns],
        **kwargs,
    )


def densify_time_index(df: pd.DataFrame) -> pd.DataFrame:
    new_index = pd.period_range(df.index.min(), df.index.max(), freq=df.index.freq)
    return df.reindex(new_index, fill_value=0)


def rollup_accounts(series: pd.Series) -> pd.Series:
    rollup = defaultdict(lambda: D(0))
    series = series[series.notna()]  # nan's can be issues??
    for account, val in series.items():

        splits = account.split(":")
        for i in range(len(splits)):
            this = ":".join(splits[: i + 1])
            rollup[this] += val

    accounts, vals = zip(*rollup.items())
    return pd.Series(data=vals, index=accounts, name=series.name)


def treeify_accounts(accounts):
    if isinstance(accounts, str):
        splits = accounts.split(":")
        if len(splits) == 1:
            return accounts
        # return "\u2588" * 2 * (len(splits) - 1) + splits[-1]
        return "\u00A0" * 2 * (len(splits) - 1) + splits[-1]
        # return ("│ " * (len(splits) - 2)) + "├ " + splits[-1]
        # return ("--" * (len(splits) - 2)) + "-|" + splits[-1]
        # return "│" * (len(splits) - 1) + " " + splits[-1]
        # return ":" * (len(splits) - 1) + " " + splits[-1]
        # return "| " * (len(splits) - 1) + splits[-1]
    return [treeify_accounts(a) for a in accounts]


def interval_plot(
    x,
    y,
    interval: Interval = Interval.MONTH,
    fig: go.Figure = None,
    **bar_kwargs,
) -> go.Figure:

    match interval:
        case Interval.DAY:
            xperiod = 1000 * 60 * 60 * 24
            # tickformat = "%d\n%Y-%m"
            dtick = None
            tickformat = None
        case Interval.WEEK:
            xperiod = 1000 * 60 * 60 * 24 * 7
            # tickformat = "%d\n%Y-%m"
            dtick = None
            tickformat = None
        case Interval.MONTH:
            xperiod = "M1"
            dtick = xperiod
            tickformat = "%b\n%Y"
        case Interval.QUARTER:
            xperiod = "M3"
            tickformat = "Q%q\n%Y"
            dtick = xperiod
        case Interval.YEAR:
            xperiod = "M12"
            tickformat = "%Y"
            dtick = xperiod
        case _:
            raise ValueError("Unknonw interval {}".format(interval))
    now = date.today()
    # pastx = []
    # pasty = []
    # futurex = []
    # futurey = []

    # for xx, yy in zip(x, y):
    #     if xx <= now:
    #         pastx.append(xx)
    #         pasty.append(yy)
    #     else:
    #         futurex.append(xx)
    #         futurey.append(yy)

    # assert fig is None
    fig = fig or go.Figure()

    # if pastx:
    #     fig.add_trace(
    #         go.Bar(
    #             x=pastx,
    #             y=pasty,
    #             xperiod=xperiod,
    #             color=color,
    #             xperiodalignment="middle",
    #             **bar_kwargs,
    #         )
    #     )
    # if futurex:
    #     fig.add_trace(
    #         go.Bar(
    #             x=futurex,
    #             y=futurey,
    #             xperiod=xperiod,
    #             color=color,
    #             xperiodalignment="middle",
    #             opacity=0.5,
    #             **bar_kwargs,
    #         )
    #     )
    # print(x)
    # print(x)
    fig.add_trace(
        go.Bar(x=x, y=y, xperiod=xperiod, xperiodalignment="middle", **bar_kwargs)
    )
    # fig = px.bar(
    #     x=[get_prev_interval(xx, interval) for xx in x],
    #     y=y,
    #     opacity=[1.0 if xx <= now else 0.5 for xx in x],
    #     # xperiod=xperiod,
    #     # xperiodalignment="middle",
    #     **bar_kwargs,
    # )
    fig.update_xaxes(
        showgrid=True,
        ticklabelmode="period",
        dtick=dtick,
        tickformat=tickformat,
    )

    return fig
