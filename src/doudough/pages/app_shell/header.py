import dash_mantine_components as dmc
from beancount.core.data import Transaction
from dash import dcc, callback, Output
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
from fava.application import _slug
from fava.util.date import Interval

from .controls import (
    TIME_SELECTOR,
    UPDATE_INTERVAL,
    SEARCH,
    BFILE,
    LOADED,
    INTERVAL,
    ACCOUNT,
    FILTER,
    get_loader,
    get_ledger,
)

# with open(os.path.join(os.path.dirname(__file__), "doudou.jpg"), "rb") as _f:
#     icon_src = "data:image/png;base64," + base64.b64encode(_f.read()).decode()

SIZE = "xs"


def label_account(account: str) -> str:
    splits = account.split(":")

    return "| " * (len(splits) - 1) + splits[-1]


_FILTER_KWARGS = dict(
    persistence=1,  # unclear what this number means
    debounce=True,
    size=SIZE,
)

LINE_SIZE = 2

layout = dmc.AppShellHeader(
    dmc.Group(
        [
            # dmc.Burger(
            #     id="burger",
            #     size=SIZE,
            #     color="green",
            #     lineSize=LINE_SIZE,
            #     # hiddenFrom="sm",
            #     opened=True,
            # ),
            dmc.Loader(
                dmc.Avatar(
                    # src="https://avatars.githubusercontent.com/u/22910810?v=4", h=40
                    # src=icon_src,
                    src="/assets/doudou.png",
                    size=SIZE,
                    # h=40,
                ),
                id="loader",
                # color="green",
            ),
            UPDATE_INTERVAL.make_widget(dcc.Interval),
            BFILE.make_widget(
                dmc.Select,
                size=SIZE,
                placeholder="Ledger File",
                clearable=False,
                leftSection=DashIconify(icon="material-symbols:edit-document"),
            ),
            # dmc.Title(
            #     "DouDough",  # TODO: use title
            #     c="green",
            #     size=SIZE,
            # ),
            # dmc.Loader(id="my_loader", variant="bars", c="red"),
            dmc.Breadcrumbs(
                children=[
                    dcc.Link(
                        "Home",
                        href="/",
                        refresh=False,
                    )
                ],
            ),
            dmc.Container(fluid=True),
            LOADED.make_widget(
                dmc.Badge,
                variant="dot",
            ),
            # CONTEXT.make_widget(),
            SEARCH.make_widget(
                # refresh="callback-nav",
                refresh=False,
            ),
            # FILTERING.make_widget(
            #     dmc.Loader,
            #     color="green",
            #     size=SIZE,
            #     # loading=False,
            #     type="bars",
            # ),
            # CONVERSION.make_widget(
            #     dmc.Select,
            #     w=100,
            #     data=DEFAULT_CONVERSIONS,
            #     value="at_cost",
            #     clearable=False,
            #     placeholder="Conversion",
            #     leftSection=DashIconify(icon="material-symbols:currency-exchange"),
            #     **_FILTER_KWARGS,
            # ),
            INTERVAL.make_widget(
                # dmc.SegmentedControl,
                dmc.Select,
                w=120,
                # label="Time Bucket",
                # placeholder="Time",
                leftSection=DashIconify(icon="material-symbols:bar-chart"),
                data=[
                    {"value": interval, "label": interval.label}
                    for interval in [
                        Interval.DAY,
                        Interval.WEEK,
                        Interval.MONTH,
                        Interval.QUARTER,
                        Interval.YEAR,
                    ]
                ],
                **_FILTER_KWARGS,
            ),
            TIME_SELECTOR.make_widget(
                dmc.TextInput,
                w=150,
                placeholder="Time",
                leftSection=DashIconify(icon="material-symbols:calendar-month"),
                **_FILTER_KWARGS,
            ),
            # dmc.HoverCardDropdown(
            #     [
            #         dmc.MonthPickerInput(
            #             placeholder="Months",
            #             allowSingleDateInRange=True,
            #             type="range",
            #             clearable=True,
            #         ),
            #         dmc.YearPickerInput(
            #             leftSection=DashIconify(icon="fa:calendar"),
            #             # label="Year",
            #             placeholder="Years",
            #             allowSingleDateInRange=True,
            #             type="range",
            #             clearable=True,
            #         ),
            #     ]
            # ),
            ACCOUNT.make_widget(
                dmc.Select,
                searchable=True,
                w=200,
                clearable=True,
                placeholder="Account",
                leftSection=DashIconify(icon="material-symbols:account-balance"),
                **_FILTER_KWARGS,
            ),
            FILTER.make_widget(
                dmc.TagsInput,
                w=200,
                placeholder="Filter by tag, payee, ...",
                leftSection=DashIconify(icon="material-symbols:tag"),
                persistence=1,
                size=SIZE,
            ),
            # dmc.Burger(
            #     id="burger_aside",
            #     size=SIZE,
            #     color="grey",
            #     opened=True,
            #     lineSize=LINE_SIZE,
            # ),
        ],
        h="100%",
        px="md",
    )
)


@callback(
    # CONVERSION.output,
    # Output(CONVERSION.id, "data"),
    Output(ACCOUNT.id, "data"),
    Output(FILTER.id, "data"),
    BFILE.input,
)
def update_autocompletes(bfile):
    ledger = get_ledger(bfile)
    ops = ledger.options["operating_currency"]
    if isinstance(ops, str):
        ops = [ops]
    tags = set()
    for entry in ledger.all_entries:
        if isinstance(entry, Transaction):
            tags.update(["#" + t for t in entry.tags])
            tags.update(["^" + l for l in entry.links])
            if entry.payee:
                tags.update(['payee:"{}"'.format(entry.payee)])
    # return [
    #     {"value": acct, "label": label_account(acct)}
    #     for acct in sorted(ledger.accounts.keys())
    # ], sorted(tags)

    return (
        # DEFAULT_CONVERSIONS
        # + [{"value": curr, "label": "Converted to {}".format(curr)} for curr in ops],
        sorted(ledger.accounts.keys()),
        sorted(tags),
    )


# @callback(SEARCH.output, TIME_SELECTOR.output, SEARCH.input, TIME_SELECTOR.input)
# def update_time(qs, time_selection):
#     trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
#     parsed = parse_qs(qs.lstrip("?"))
#     match trigger_id:
#         case TIME_SELECTOR.id:
#             nt = time_selection
#
#             if time_selection:
#                 if time_selection == parsed.get("time", ""):
#                     raise PreventUpdate
#                 parsed["time"] = time_selection
#             else:
#                 if "time" in parsed:
#                     del parsed["time"]
#                 else:
#
#                     raise PreventUpdate
#
#             nq = urlencode(parsed)
#             if not nq.startswith("?"):
#                 nq = "?" + nq
#
#         case SEARCH.id:
#             nq = qs
#             nt = parsed.get("time", "")
#             if nt == time_selection:
#                 raise PreventUpdate
#         case _:
#             raise ValueError(trigger_id)
#     return nq, nt


#
#
# @callback(ACCOUNT.output, FILTER.output, TIME_SELECTOR.output, SEARCH.input)
# def update_search_controls(qs):
#     f = request.args.get("filter", "")
#     if f:
#         f = list(f.split())
#     else:
#         f = []
#     return (
#         request.args.get("account", ""),
#         f,
#         request.args.get("time", ""),
#     )


@callback(
    BFILE.output,
    BFILE.make_output("data"),
    BFILE.state,
    UPDATE_INTERVAL.input,
)
def first_load_metadata(current_slug, interval):

    loader = get_loader()
    if current_slug in loader.ledgers_by_slug:
        raise PreventUpdate()
    else:
        new_slug = loader.first_slug()

    return new_slug, [_slug(ledger) for ledger in loader.ledgers]
