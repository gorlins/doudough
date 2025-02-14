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
    WIDGET_CLASS: type = None

    def __init__(self, id, **kwargs):
        self.id = id
        for k in self._COPY_VALS or tuple():
            setattr(self, k, kwargs.pop(k, None))

    def make_output(self, property):
        return Output(self.id, property)

    def make_input(self, property):
        return Input(self.id, property)

    def make_state(self, property):
        return State(self.id, property)

    @property
    def output(self):
        return self.make_output(self.MAIN_ATTRIBUTE)

    @property
    def input(self):
        return self.make_input(self.MAIN_ATTRIBUTE)

    @property
    def state(self):
        return self.make_state(self.MAIN_ATTRIBUTE)

    def make_widget(self, widget_class=None, copy=None, **kwargs):
        widget_class = widget_class or self.WIDGET_CLASS
        if widget_class is None:
            raise TypeError("Need to specify widget_class or cls.WIDGET_CLASS")

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
    WIDGET_CLASS = dcc.Graph


class Control(CallbackHelper):
    _COPY_VALS = ("value",)
    MAIN_ATTRIBUTE = "value"


class LoaderHelper(CallbackHelper):
    MAIN_ATTRIBUTE = "loading"


class SearchHelper(CallbackHelper):
    WIDGET_CLASS = dcc.Location
    MAIN_ATTRIBUTE = "search"


LEDGER_LOADER: _LedgerSlugLoader = None
LEDGER_SLUG = Control("bfile")
BFILE = LEDGER_SLUG
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
    "time",
    value="",
    # value="{} - day".format(datetime.now().year - 1),
)


@dataclass
class Context:
    """The context values for the current view

    Unlike Fava, this is not used for flask.g, as Dash will serialize the context (??) and slow things down
    """

    #: Slug for the active Beancount file.
    bfile: str = None

    # Filters
    time: str = None
    account: str = None
    filter: str = None

    # Other
    # interval: str = "month"
    # conversion: str = "at_cost"

    @property
    def operating_currency(self) -> str:
        all_oc = self.operating_currencies
        if len(all_oc) > 1:
            raise NotImplementedError()
        return all_oc[0]

    @property
    def operating_currencies(self) -> list:
        return self.ledger.options.get("operating_currency", [])

    @property
    def ledger(self) -> FavaLedger:
        return get_ledger(self.bfile)

    # @property
    # def typed_conversion(self) -> Conversion:
    #     """Conversion to apply (raw string)."""
    #     return conversion_from_str(self.conversion or "at_cost")
    #
    # @property
    # def typed_interval(self) -> Interval:
    #     """Interval to group by."""
    #     return Interval.get(self.interval)

    @property
    def filtered(self) -> FilteredLedger:
        """The filtered ledger"""
        if isinstance(self.filter, list):
            f = " ".join(self.filter)
        else:
            f = ""
        return self.ledger.get_filtered(account=self.account, filter=f, time=self.time)

    # @classmethod
    # def from_urlpath(cls, path, query_string: str):
    #     if "/" in path:
    #         splits = path.split("/", 2)
    #         bfile = splits[1]
    #     else:
    #         bfile = path
    #
    #     if bfile.lower() == "none":
    #         bfile = None
    #
    #     return cls(beancount_file_slug=bfile, rargs=parse_search(query_string))


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
            "bfile": BFILE.input,
        },
        # running=[(FILTERING.output, True, False)],
        **kwargs,
    )


def ledger_callback(*args, **kwargs):
    def decorator(func):
        # First, wrap the function
        @wraps(func)
        def wrapped(*a):
            # context = Context.from_urlpath(a[-2], a[-1])
            context = Context(**a[-1])
            return func(context, *a[:-1])

        # Then, generate the callback
        return callback(*args, CONTEXT.input, **kwargs)(wrapped)

    return decorator


def group_callbacks(*callbacks):
    inputs = []
    outputs = []
    states = []
    for c in callbacks:
        if isinstance(c, Input):
            inputs.append(c)
        elif isinstance(c, Output):
            outputs.append(c)
        elif isinstance(c, State):
            states.append(c)
        else:
            raise TypeError(type(c).__name__)
    return outputs, inputs, states


def insert_callbacks(new, original):
    gn = group_callbacks(*new)
    go = group_callbacks(*original)

    for n, o in zip(gn, go):
        yield from n
        yield from o


def filtered_ledger_callback(*args, **kwargs):
    def decorator(func):
        # First, wrap the function
        @wraps(func)
        def wrapped(bfile, account, filter, time, *a):
            # context = Context.from_urlpath(a[-2], a[-1])
            context = Context(bfile=bfile, account=account, filter=filter, time=time)
            return func(context, *a)

        # Then, generate the callback
        return callback(
            *insert_callbacks(
                [
                    # *args,]
                    BFILE.input,
                    ACCOUNT.input,
                    FILTER.input,
                    TIME_SELECTOR.input,
                ],
                args,
            ),
            **kwargs,
        )(wrapped)

    return decorator


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


def parse_search(search: str) -> dict:
    parsed = parse_qs(search.lstrip("?"))
    return {k: v[0] for k, v in parsed.items()}


def get_filtered_ledger(
    account=None, filter=None, time=None, slug=None, **ignore
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


def ledger_layout(func):
    @wraps(func)
    def wrapped(
        bfile=None,
        **kwargs,
    ):
        if bfile is None:
            return "No ledger loaded!"

        return func(ledger=get_ledger(bfile), **kwargs)

    return wrapped
