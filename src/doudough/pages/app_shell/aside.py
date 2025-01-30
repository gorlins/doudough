import dash_mantine_components as dmc
from dash import callback, Input, Output, State


layout = dmc.AppShellAside("Aside", p="md", id="aside")


@callback(
    Output("appshell", "aside"),
    Input("burger_aside", "opened"),
    State("appshell", "aside"),
)
def toggle_navbar(opened, navbar):
    navbar["collapsed"] = {"desktop": not opened}
    return navbar
