"""The command-line interface for doudough."""

import logging
import os
from pathlib import Path

import click
from fava import __version__
from fava.cli import NonAbsolutePathError, NoFileSpecifiedError

from .app import app, create_app


def _add_env_filenames(filenames: tuple[str, ...]) -> tuple[str, ...]:
    """Read additional filenames from BEANCOUNT_FILE."""
    env_filename = os.environ.get("BEANCOUNT_FILE")
    if not env_filename:
        return tuple(dict.fromkeys(filenames))

    env_names = env_filename.split(os.pathsep)
    for name in env_names:
        if not Path(name).is_absolute():
            raise NonAbsolutePathError(name)

    all_names = tuple(env_names) + filenames
    return tuple(dict.fromkeys(all_names))


@click.command(context_settings={"auto_envvar_prefix": "FAVA"})
@click.argument(
    "filenames",
    nargs=-1,
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
)
@click.option(
    "-p",
    "--port",
    type=int,
    default=5000,
    show_default=True,
    metavar="<port>",
    help="The port to listen on.",
)
@click.option(
    "-H",
    "--host",
    type=str,
    default="localhost",
    show_default=True,
    metavar="<host>",
    help="The host to listen on.",
)
# @click.option("--prefix", type=str, help="Set an URL prefix.")
@click.option(
    "--incognito",
    is_flag=True,
    help="Run in incognito mode and obscure all numbers.",
)
@click.option(
    "--read-only",
    is_flag=True,
    help="Run in read-only mode, disable any change through Fava.",
)
@click.option("-d", "--debug", is_flag=True, help="Turn on debugging.")
@click.option(
    "--profile",
    is_flag=True,
    help="Turn on profiling. Implies --debug.",
)
@click.option(
    "--profile-dir",
    type=click.Path(),
    help="Output directory for profiling data.",
)
@click.option("--poll-watcher", is_flag=True, help="Use old polling-based watcher.")
@click.version_option(version=__version__, prog_name="fava")
def main(  # noqa: PLR0913
    *,
    filenames: tuple[str, ...] = (),
    port: int = 5000,
    host: str = "localhost",
    prefix: str | None = None,
    incognito: bool = False,
    read_only: bool = False,
    debug: bool = False,
    profile: bool = False,
    profile_dir: str | None = None,
    poll_watcher: bool = False,
) -> None:  # pragma: no cover
    """Start Doudough for FILENAMES on http://<host>:<port>.

    If the `BEANCOUNT_FILE` environment variable is set, Fava will use the
    files (delimited by ';' on Windows and ':' on POSIX) given there in
    addition to FILENAMES.

    Note you can also specify command-line options via environment variables
    with the `FAVA_` prefix. For example, `--host=0.0.0.0` is equivalent to
    setting the environment variable `FAVA_HOST=0.0.0.0`.
    """
    all_filenames = _add_env_filenames(filenames)

    if not all_filenames:
        raise NoFileSpecifiedError

    create_app(
        all_filenames,
        # incognito=incognito,
        # read_only=read_only,
        # poll_watcher=poll_watcher,
        fava_app=app.server,
    )

    # if prefix:
    #     app.wsgi_app = DispatcherMiddleware(  # type: ignore[method-assign]
    #         simple_wsgi,
    #         {prefix: app.wsgi_app},
    #     )

    # ensure that cheroot does not use IP6 for localhost
    host = "127.0.0.1" if host == "localhost" else host
    # Debug mode if profiling is active
    debug = debug or profile

    click.secho(f"Starting Fava on http://{host}:{port}", fg="green")
    if not debug:
        pass
    else:
        logging.getLogger("fava").setLevel(logging.DEBUG)

    app.run(debug=debug)
