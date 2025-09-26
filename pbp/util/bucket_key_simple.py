from urllib.parse import ParseResult


def get_bucket_key_simple(parsed_uri: ParseResult) -> tuple[str, str, str]:
    """
    Extract bucket, key, and simple filename from a parsed cloud storage URI.

    Args:
        parsed_uri: A parsed URI for a cloud storage resource (s3://, gs://, etc.)

    Returns:
        A tuple of (bucket, key, simple_filename) where:
        - bucket: The storage bucket name
        - key: The full object key/path
        - simple_filename: Just the filename part (last component of the path)
    """
    bucket = parsed_uri.netloc
    key = parsed_uri.path.lstrip("/")
    simple = key.split("/")[-1] if "/" in key else key
    assert "/" not in simple, f"Unexpected simple_filename: '{simple}'"
    return bucket, key, simple
