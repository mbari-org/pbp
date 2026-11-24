import os
from typing import Optional, Union
from urllib.parse import ParseResult, unquote, urlparse


def is_local_scheme(scheme: str, windows: Optional[bool] = None) -> bool:
    """
    Tells whether a scheme, as given by `urlparse`, denotes a local file.

    Args:
        scheme: The scheme: "" for a plain path, "file" for a `file://` URI.
            On Windows, a one-letter scheme is a drive letter (e.g., "C:\\...").
        windows: Whether to apply Windows conventions.
            By default, determined from the running OS.

    Returns:
        True if local.
    """
    if windows is None:
        windows = os.name == "nt"
    return scheme in ("", "file") or (windows and len(scheme) == 1)


def file_uri_to_path(uri: Union[str, ParseResult], windows: Optional[bool] = None) -> str:
    """
    Converts a `file://` URI (or a plain path) to a local filesystem path.

    On Windows, handles the various forms of a drive-based location:
      - `file:///C:/path`  -> `C:/path`
      - `file://C:/path`   -> `C:/path`
      - `C:/path`, `C:\\path` (plain path, parsed by urlparse with "c" as scheme)
    with percent-encoded characters decoded (e.g., `%20` -> space).

    Elsewhere:
      - `file:///abs/path` -> `/abs/path`
      - `file://rel/path`  -> `rel/path`
      - `some/path`, `/abs/path` (plain path) -> as given

    Args:
        uri: The URI (or plain path) to convert, or its parsed form.
        windows: Whether to apply Windows conventions.
            By default, determined from the running OS.

    Returns:
        The local path.
    """
    parsed = uri if isinstance(uri, ParseResult) else urlparse(uri)
    if windows is None:
        windows = os.name == "nt"

    if windows:
        # Plain Windows path misinterpreted by urlparse as having a scheme:
        # "C:/path" -> scheme="c", path="/path", netloc=""
        if len(parsed.scheme) == 1 and parsed.scheme.isalpha() and not parsed.netloc:
            # urlparse lowercases the scheme, so we uppercase it back:
            return unquote(parsed.scheme.upper() + ":" + parsed.path)

        # file:///C:/path -> path="/C:/path", netloc=""
        # file://C:/path  -> path="/path", netloc="C:"
        full_path = unquote(parsed.netloc + parsed.path)
        # Remove leading slash before a drive letter ("/C:/..." -> "C:/..."):
        if len(full_path) >= 3 and full_path[0] == "/" and full_path[2] == ":":
            full_path = full_path[1:]
        return full_path

    # "file://rel/path" -> netloc="rel", path="/path"
    # "file:///abs/path" -> netloc="", path="/abs/path"
    return parsed.netloc + parsed.path
