"""Doudough app shell""" ""
import importlib
import os
import os.path
from pathlib import Path
from typing import Iterable

import dash_mantine_components as dmc
from dash import (
    Dash,
    register_page,
    page_container,
    _dash_renderer,
)
from dash_iconify import DashIconify
from flask import Flask
from flask_babel import Babel

from .pages import home
from .pages.app_shell import header, navbar

# Required for dash_mantine_components
_dash_renderer._set_react_version("18.2.0")


def get_icon(icon, height=16, **kwargs):
    return DashIconify(icon=icon, height=height, **kwargs)


def create_app(
    files: Iterable[Path | str],
    *,
    # load: bool = False,
    incognito: bool = False,
    # read_only: bool = False,
    fava_app=None,
) -> Flask:
    """Create a doudough Flask application.

    Arguments:
        files: The list of Beancount files (paths).
        load: Whether to load the Beancount files directly.
        incognito: Whether to run in incognito mode.
        read_only: Whether to run in read-only mode.
    """

    # Taken from fava.application.create_app, disabling the fava parts that dash does not need
    # fava_app = fava_app or Flask("doudough")
    # fava_app.register_blueprint(json_api, url_prefix="/<bfile>/api")
    # fava_app.json = FavaJSONProvider(fava_app)
    # fava_app.app_ctx_globals_class = Context  # type: ignore[assignment]
    # _setup_template_config(fava_app, incognito=incognito)
    # _setup_babel(fava_app)  # Requires g.ledger to be non-null
    Babel(fava_app)
    # _setup_filters(fava_app, read_only=read_only)
    # _setup_routes(fava_app)

    # fava_app.config["HAVE_EXCEL"] = HAVE_EXCEL
    fava_app.config["BEANCOUNT_FILES"] = [os.path.abspath(str(f)) for f in files]
    # fava_app.config["INCOGNITO"] = incognito
    # Don't load this - slows down serialization?? create ledger another way using global functions
    # fava_app.config["LEDGERS"] = _LedgerSlugLoader(
    #     fava_app,
    #     load=load,
    # )
    return fava_app


# server = create_app(["personal.beancount"])
app = Dash(
    external_stylesheets=dmc.styles.ALL,
    use_pages=True,
    assets_folder=os.path.join(os.path.dirname(__file__), "assets"),
    pages_folder="",
    # server=server,
    # suppress_callback_exceptions=True,  # This breaks ledger loading??
    # routing_callback_inputs={
    #     # The language will be passed as a `layout` keyword argument to page layout functions
    #     "bfile": LEDGER_SLUG.input,
    # },
)

# create_app(["personal.beancount"], fava_app=app.server)

dmc.add_figure_templates(default="mantine_light")
ICON_STYLE = "-rounded"

order = 0
register_page(
    home.__name__,
    layout=home.layout,
    path="/",
    order=order,
    icon="material-symbols:home-work" + ICON_STYLE,
)


for module, icon in [
    ("income_statement", "material-symbols:bar-chart" + ICON_STYLE),
    ("balance_sheet", "material-symbols:area-chart" + ICON_STYLE),
    ("journal", "material-symbols:lists" + ICON_STYLE),
    ("payee_renamer", "material-symbols:account-balance" + ICON_STYLE),
    ("errors", "material-symbols:error" + ICON_STYLE),
    ("options", "material-symbols:settings" + ICON_STYLE),
]:
    order += 1
    lib = "doudough.pages." + module
    imported = importlib.import_module(lib)
    register_page(
        lib,
        layout=getattr(imported, "layout"),
        order=order,
        path_template="/<bfile>/" + module,
        # path_template="/" + module,
        icon=icon,
    )


shell = dmc.AppShell(
    [
        header.layout,
        navbar.layout(),  # Create after pages have registered
        dmc.AppShellMain(page_container),
        # aside.layout,
        # footer.layout,
    ],
    header={"height": 40},
    # footer={
    #     "height": 40,
    #     # "collapsed": True,
    # },
    navbar={
        "width": 220,
        "breakpoint": "sm",
        "collapsed": {"mobile": True},
    },
    # aside={
    #     "width": 300,
    #     "breakpoint": "md",
    #     "collapsed": {"desktop": False, "mobile": True},
    # },
    padding="md",
    id="appshell",
)
layout = dmc.MantineProvider(shell, theme={"primaryColor": "green"})


app.layout = layout
