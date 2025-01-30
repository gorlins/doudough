import dash_mantine_components as dmc
from dash import dcc
from dash_iconify import DashIconify
from fava.util.date import Interval

from .controls import (
    TIME_SELECTOR,
    INTERVAL,
    ACCOUNT,
    OPERATING_CURRENCY,
    FILTER,
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


layout = dmc.AppShellHeader(
    dmc.Group(
        [
            dmc.Burger(
                id="burger",
                size=SIZE,
                color="green",
                # hiddenFrom="sm",
                opened=True,
            ),
            # dmc.Avatar(
            #     # src="https://avatars.githubusercontent.com/u/22910810?v=4", h=40
            #     src=icon_src,
            #     size=SIZE,
            #     # h=40,
            # ),
            dmc.Title(
                "DouDough",  # TODO: use title
                c="green",
                size=SIZE,
            ),
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
            # SEARCH.make_location(refresh="callback-nav"),
            # FILTERING.make_widget(
            #     dmc.Loader,
            #     color="green",
            #     size=SIZE,
            #     # loading=False,
            #     type="bars",
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
            dmc.HoverCard(
                children=[
                    dmc.HoverCardTarget(
                        TIME_SELECTOR.make_widget(
                            dmc.TextInput,
                            w=150,
                            placeholder="Time",
                            leftSection=DashIconify(
                                icon="material-symbols:calendar-month"
                            ),
                            **_FILTER_KWARGS,
                        )
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
                ]
            ),
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
            OPERATING_CURRENCY.make_widget(
                dmc.TextInput,
                w=100,
                placeholder="Operating Currency",
                leftSection=DashIconify(icon="material-symbols:currency-exchange"),
                **_FILTER_KWARGS,
            ),
            dmc.Burger(
                id="burger_aside",
                size=SIZE,
                color="grey",
                opened=True,
            ),
        ],
        h="100%",
        px="md",
    )
)

#
# # @callback()
# @callback(
#     Output(ACCOUNT.id, "data"),
#     Output(FILTER.id, "data"),
#     LEDGER_SLUG.input,
#     # LOADED.input,
# )
# def update_autocompletes(ledger_slug):
#     ledger = get_ledger(ledger_slug)
#     tags = set()
#     for entry in ledger.all_entries:
#         if isinstance(entry, Transaction):
#             tags.update(["#" + t for t in entry.tags])
#             tags.update(["^" + l for l in entry.links])
#             if entry.payee:
#                 tags.update(['payee:"{}"'.format(entry.payee)])
#     # return [
#     #     {"value": acct, "label": label_account(acct)}
#     #     for acct in sorted(ledger.accounts.keys())
#     # ], sorted(tags)
#
#     return sorted(ledger.accounts.keys()), sorted(tags)


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
