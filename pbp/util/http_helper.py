from urllib.request import Request, urlopen


def read_url_head(url: str, num_bytes: int = 20_000) -> tuple[bytes, int]:
    """
    Reads the first bytes of a remote file with a single ranged GET request.

    Args:
        url (str): The http(s) URL of the file.
        num_bytes (int): Number of bytes to read from the start of the file.

    Returns:
        tuple[bytes, int]: The head bytes (fewer than `num_bytes` if the file
        is smaller), and the total size of the file in bytes.
    """
    request = Request(url, headers={"Range": f"bytes=0-{num_bytes - 1}"})
    with urlopen(request) as response:
        head = response.read(num_bytes)
        # On a 206 response, Content-Range is "bytes 0-N/TOTAL".
        content_range = response.headers.get("Content-Range")
        if content_range is not None:
            total = int(content_range.rsplit("/", 1)[-1])
        else:
            # Range not honored by the server: a 200 with the full content length.
            total = int(response.headers["Content-Length"])
    return head, total
