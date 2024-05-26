#!/usr/bin/env python
import sys
from enum import Enum
from pprint import pprint
from typing import Optional, Annotated

import typer
from rich.table import Table

from finder_sidebar_editor import FinderSidebar

FILE_LOCALHOST = "file://localhost"


# TODO move to core utils
class OutputFlavor(str, Enum):
    TXT = "txt"
    QUOTED_TXT = "quoted-txt"
    JSON = "json"
    CSV = "csv"


app = typer.Typer(no_args_is_help=True, help="""A program edit the MacOS finder sidebar.""")


@app.command()
def ls(raw: Annotated[
    Optional[bool], typer.Option(help="raw output. Maybe useful for debugging. Overrides format option.")] = False,
       output_format: Annotated[OutputFlavor, typer.Option()] = OutputFlavor.TXT):
    sidebar = FinderSidebar()
    if raw:
        pprint(sidebar.snapshot)
        exit(0)
    else:
        output_ls(sidebar.favorites, output_format)


@app.command()
def rm(name_or_path: Annotated[str, typer.Argument()],
       force: Annotated[
           Optional[bool], typer.Option(help="ignore missing favorite name, otherwise return error.")] = False,
       by_path: Annotated[Optional[bool], typer.Option()] = False):
    if not name_or_path or name_or_path.isspace():
        print_error("name or path is empty or whitespace only")
        exit(1)
    sidebar = FinderSidebar()
    if by_path:
        sidebar.remove_by_path(name_or_path)
    else:
        name = name_or_path  # for clarity
        if not force:
            sidebar.update()
            validate_name(sidebar, name)
            sidebar.remove(name_or_path)
        else:
            sidebar.remove(name_or_path)


@app.command()
def add(path: Annotated[str, typer.Argument(help="""The path to add, which must exist unless --force is used.
            If you add a path that was already added, it is effectively a noop (or appears to be?).
            The name of the favorite is the tail end of the path (i.e. /path/to/mydir gets a name mydir).
            """)],
        uri: Annotated[Optional[str], typer.Argument(
            help='If this starts with "afp" or "smb", then try to mount it first. It is an error if it MacOS cannot ' \
                 ' mount it.')] = FILE_LOCALHOST,
        order: Annotated[Optional[int], typer.Argument(
            help="Not yet implemented.  Added items are always at the top. Use mv to move them.")] = 0,
        force: Annotated[Optional[bool], typer.Option(help="""
            ignore non-existent path testing in two different ways:
            1) if only path given, make sure that path exists in the filesystem, otherwise return error. 
            2) if path and uri given, and uri starts with "afp" or "smb", then do the same with the url+path, otherwise error.
            Note that forcing the add of a path that doesnt exist may lead to a damaged item displayed as '?" in your favorites in finder
            """)] = False,
        verbose: Annotated[Optional[bool], typer.Option()] = False
        ):
    sidebar = FinderSidebar()
    if not force:
        import os
        from urllib.parse import urlparse
        if not os.path.exists(path):
            print_error(fr'"{path}" not found')
            exit(1)
        if not uri == FILE_LOCALHOST:
            p = urlparse(uri + path)
            final_path = os.path.abspath(os.path.join(p.netloc, p.path))
            if not os.path.exists(final_path):
                print_error(fr'"{final_path}" not found')
                exit(1)
    print_verbose(fr'adding "{path}" as {uri}', verbose)
    sidebar.add(path, uri)


@app.command()
def mv(to_move: Annotated[str, typer.Argument()],
       to_after: Annotated[str, typer.Argument()]):
    sidebar = FinderSidebar()
    sidebar.move(to_move, to_after)


@app.command()
def rename(from_name: Annotated[str, typer.Argument()],
           to_name: Annotated[str, typer.Argument()]):
    sidebar = FinderSidebar()
    validate_name(sidebar, from_name)
    validate_name(sidebar, to_name)
    raise NotImplementedError("Not yet implemented. Underlying lib needs a method to rename an item.")


def validate_name(sidebar: FinderSidebar, name: str) -> None:
    """
    ensure the name exists in the sidebar
    Args:
        sidebar:
        name:

    """
    if not sidebar.exists(name):
        print_error(f'"{name}" not found')
        exit(1)


def output_ls(stuff: dict, output_flavor: OutputFlavor = OutputFlavor.TXT) -> None:
    if output_flavor == OutputFlavor.JSON:
        raise NotImplementedError("Not yet implemented")
        # j = json.dumps(stuff )
    else:
        sep: str = "\t\t" if output_flavor in [OutputFlavor.TXT, OutputFlavor.QUOTED_TXT] else ","
        quote: bool = output_flavor in [OutputFlavor.QUOTED_TXT or OutputFlavor.CSV]
        if output_flavor == OutputFlavor.CSV:
            for item in stuff.items():
                print(f'"{item[0]}","{item[1]}"')
        else:
            t = Table(box=None, show_edge=False, show_header=False)
            from rich.console import Console
            c = Console()
            for item in stuff.items():
                if not quote:
                    t.add_row(str(item[0]), str(item[1]))
                else:
                    t.add_row(f'"{item[0]}"', f'"{item[1]}"')
            c.print(t)


def print_error(msg: str) -> None:
    print(msg, file=sys.stderr)


def print_verbose(msg: str, verbose: bool):
    if verbose:
        print(msg)


if __name__ == "__main__":
    app()
