from functools import wraps
from typing import Tuple

from dash import Input, Output, dcc, callback
from fava.application import _LedgerSlugLoader
from fava.core import FavaLedger, FilteredLedger
from fava.util.date import Interval
from flask import current_app


class CallbackHelper:
    _COPY_VALS: tuple = tuple()
    MAIN_ATTRIBUTE: str = ""

    def __init__(self, id, **kwargs):
        self.id = id
        for k in self._COPY_VALS or tuple():
            setattr(self, k, kwargs.pop(k, None))

    def make_output(self, property):
        return Output(self.id, property)

    def make_input(self, property):
        return Input(self.id, property)

    @property
    def output(self):
        return self.make_output(self.MAIN_ATTRIBUTE)

    @property
    def input(self):
        return self.make_input(self.MAIN_ATTRIBUTE)

    def make_widget(self, widget_class, copy=None, **kwargs):
        for k in copy or self._COPY_VALS:
            kwargs[k] = getattr(self, k)
        return widget_class(id=self.id, **kwargs)


class IntervalHelper(CallbackHelper):
    MAIN_ATTRIBUTE = "interval"


class DataHelper(CallbackHelper):
    MAIN_ATTRIBUTE = "data"
    _COPY_VALS = ("data",)


class ChildrenHelper(CallbackHelper):
    _COPY_VALS = ("children",)
    MAIN_ATTRIBUTE = "children"


class GraphHelper(CallbackHelper):
    MAIN_ATTRIBUTE = "figure"

    def make_graph(self, **kwargs):
        return self.make_widget(dcc.Graph, **kwargs)


class Control(CallbackHelper):
    _COPY_VALS = ("value",)
    MAIN_ATTRIBUTE = "value"


class LoaderHelper(CallbackHelper):
    MAIN_ATTRIBUTE = "loading"


class SearchHelper(CallbackHelper):
    MAIN_ATTRIBUTE = "search"

    def make_location(self, **kwargs):
        return self.make_widget(dcc.Location, **kwargs)


LEDGER_LOADER: _LedgerSlugLoader = None
LEDGER_SLUG = Control("ledger_slug")
OPERATING_CURRENCY = Control("operating_currency", value="USD")
UPDATE_INTERVAL = IntervalHelper("update_interval")
ENTRIES = Control("ledger_entries")
ERRORS = Control("ledger_errors")
OPTIONS_MAP = Control("ledger_options")
LOADED = ChildrenHelper("ledger_loaded", children="")
FILTERING = LoaderHelper("applying_filter")
# SEARCH = SearchHelper("location")
INTERVAL = Control("interval", value=Interval.MONTH)
ACCOUNT = Control("account")
FILTER = Control("filter", value=[])
TIME_SELECTOR = Control(
    "time_selection",
    value="",
    # value="{} - day".format(datetime.now().year - 1),
)


# @callback(
#     OPERATING_CURRENCY.output,
#     LOADED.output,
#     LEDGER_FILE.input,
# )
# def load_data(ledger_file):
#     # ledger = g.ledger
#     # global LEDGER
#     # global FILTERED_LEDGER
#     g.ledger = FavaLedger(os.path.abspath(ledger_file))
#     # FILTERED_LEDGER = LEDGER.get_filtered()
#     # return context.operating_currency, datetime.now()
#     return "USD", datetime.now()


def get_loader():
    # Avoid caching on flask.g - might hurt dash serialization??
    global LEDGER_LOADER
    if LEDGER_LOADER is None:
        LEDGER_LOADER = _LedgerSlugLoader(current_app)
    return LEDGER_LOADER


def filtered_callback(*args, **kwargs):
    return callback(
        *args,
        {
            "account": ACCOUNT.input,
            "filter": FILTER.input,
            "time": TIME_SELECTOR.input,
            "slug": LEDGER_SLUG.input,
        },
        # running=[(FILTERING.output, True, False)],
        **kwargs,
    )


# def get_ledger():
#     loader = current_app.config["LEDGERS"]
#     try:
#         return g.ledger
#     except AttributeError:
#         try:
#             slug = g.beancount_file_slug or loader.first_slug()
#         except AttributeError:
#             slug = loader.first_slug()
#             g.beancount_file_slug = slug
#         g.ledger = loader.ledgers_by_slug[slug]


def get_ledger(slug=None):

    loader = get_loader()
    slug = slug or loader.first_slug()
    return loader[slug]


def get_filtered_ledger(
    account=None, filter=None, time=None, slug=None
) -> Tuple[FavaLedger, FilteredLedger]:
    ledger = get_ledger(slug=slug)
    return ledger, ledger.get_filtered(
        account=account or "",
        filter=" ".join(filter) if filter is not None else "",
        time=(
            time
            if isinstance(time, str)
            else time[0] if isinstance(time, (list, tuple)) else ""
        ),
    )


def default_file(func):
    @wraps(func)
    def wrapped(bfile=None, **kwargs):
        if not bfile:
            try:
                bfile = get_loader().first_slug()
            except RuntimeError:
                # not part of a flask request, ignore
                bfile = ""

        return func(bfile=bfile, **kwargs)

    return wrapped
