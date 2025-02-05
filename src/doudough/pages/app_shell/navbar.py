import dash_mantine_components as dmc
from dash import page_registry, callback, Input, Output, State, callback_context, ALL
from dash_iconify import DashIconify

from .controls import LEDGER_SLUG
from ..utils import fill_url


# @default_file
#
# # Ensure we keep any query args
# try:
#     ref = request.headers.get("Referer")
#
#     split = urlsplit(ref)
#
#     parts = []
#     if split.query:
#         parts.append("?")
#         parts.append(split.query)
#     if split.fragment:
#         parts.append("#")
#         parts.append(split.fragment)
#     query = "".join(parts)
#
# except RuntimeError:
#     query = ""


def layout(**kwargs):
    return dmc.AppShellNavbar(
        id="navbar",
        children=[
            # "Navbar",
            *[
                dmc.NavLink(
                    label=page["name"],
                    href=page["relative_path"],  # + query,
                    id={
                        "type": "navlink",
                        "index": page["path_template"] or page["relative_path"],
                    },
                    refresh=False,
                    leftSection=(
                        DashIconify(icon=page["icon"]) if "icon" in page else None
                    ),
                )
                for page in page_registry.values()
            ]
        ],
        p="md",
    )


@callback(
    Output("appshell", "navbar"),
    Input("burger", "opened"),
    State("appshell", "navbar"),
)
def toggle_navbar(opened, navbar):
    navbar["collapsed"] = {"desktop": not opened}
    return navbar


# Callback (using the dcc.location provided by Dash Pages)
@callback(
    Output({"type": "navlink", "index": ALL}, "active"),
    Input("_pages_location", "pathname"),
    LEDGER_SLUG.input,
)
def set_active_link(pathname, bfile):
    return [
        pathname == fill_url(control["id"]["index"], bfile=bfile)
        for control in callback_context.outputs_list
    ]


@callback(
    Output({"type": "navlink", "index": ALL}, "href"),
    Input("_pages_location", "pathname"),
    LEDGER_SLUG.input,
)
def update_navlinks(pathname, slug):
    # print([c["id"]["index"] for c in callback_context.outputs_list])

    return [
        fill_url(link["id"]["index"], bfile=slug)
        for link in callback_context.outputs_list
    ]
