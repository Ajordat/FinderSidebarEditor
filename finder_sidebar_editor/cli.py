#!/usr/bin/env python
import sys
from enum import Enum
from pprint import pprint
from typing import Optional, Annotated

import typer
import rich
from rich.table import Table

from finder_sidebar_editor import FinderSidebar

FILE_LOCALHOST = "file://localhost"


# TODO move to core utils
class OutputFlavor(str,Enum):
    TXT = "txt"
    QUOTED_TXT="quoted-txt"
    JSON = "json"
    CSV = "csv"


app = typer.Typer(no_args_is_help=True, help="""A program edit the MacOS finder sidebar.""")


@app.command()
def ls(raw: Annotated[
    Optional[bool], typer.Option(help="raw output. Maybe useful for debugging. Overrides format option.")] = False,
       output_format: Annotated[OutputFlavor, typer.Option()] = OutputFlavor.TXT):
    if None:
        sidebar = FinderSidebar()
        sidebar.remove("All My Files")  # Remove 'All My Files' favorite from sidebar
        sidebar.remove("iCloud")  # Remove 'iCloud' favorite from sidebar
        sidebar.add("/Library")  # Add '/Library' favorite to sidebar
        sidebar.add("/SomeShare",
                    uri="smb://shares")  # Mount 'smb://shares/SomeShare' to '/Volumes/SomeShare' and add as favorite to sidebar
        sidebar.add("/SomeOtherShare",
                    uri="afp://username:pw@server")  # Mount pw protected 'afp://server/SomeOtherShare' to '/Volumes/SomeOtherShare' and add as favorite to sidebar
        sidebar.move("Library", "Applications")

    sidebar = FinderSidebar()
    if raw:
        pprint(sidebar.snapshot)
        exit(0)
    else:
        output(sidebar.favorites, output_format)


@app.command()
def rm(name_or_path: Annotated[str, typer.Argument()],
       force: Annotated[
           Optional[bool], typer.Option(help="ignore missing favorite name, otherwise return error.")] = False,
       by_path: Annotated[Optional[bool], typer.Option()] = False):
    sidebar = FinderSidebar()
    if by_path:
        sidebar.remove_by_path(name_or_path)
    else:
        name = name_or_path  # for clarity
        if not force:
            sidebar.update()
            validate_name(sidebar, name)
        else:
            sidebar.remove(name_or_path)


def verboseprint(parama: str, verbose: bool):
    if verbose:
        print(parama)


@app.command()
def add(path: Annotated[str, typer.Argument()],
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
            print(fr'"{path}" not found', file=sys.stderr)
            exit(1)
        if not uri == FILE_LOCALHOST:
            p = urlparse(uri + path)
            final_path = os.path.abspath(os.path.join(p.netloc, p.path))
            if not os.path.exists(final_path):
                print(fr'"{final_path}" not found', file=sys.stderr)
                exit(1)
    verboseprint(fr'adding "{path}" as {uri}', verbose)
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
    if not sidebar.exists(name):
        print(f'"{name}" not found', file=sys.stderr)
        exit(1)


def output(stuff: dict, output_flavor: OutputFlavor = OutputFlavor.TXT) -> None:
    if output_flavor == OutputFlavor.JSON:
        raise NotImplementedError("Not yet implemented")
        # j = json.dumps(stuff )
    else:
        sep: str = "\t\t" if output_flavor in [OutputFlavor.TXT, OutputFlavor.QUOTED_TXT] else ","
        quote:bool = output_flavor in [OutputFlavor.QUOTED_TXT or OutputFlavor.CSV]
        if output_flavor == OutputFlavor.CSV:
            for item in stuff.items():
                print(f'"{item[0]}","{item[1]}"')
        else:
            t = Table(box=None, show_edge=False, show_header=False)
            from rich.console import Console
            c = Console()
            for item in stuff.items():
                if quote:
                    t.add_row( str(item[0]) , str(item[1]) )
                else:
                    t.add_row( f'"{item[0]}"' , f'"{item[1]}"' )
            c.print(t)


if __name__ == "__main__":
    app()
