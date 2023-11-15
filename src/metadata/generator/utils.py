def  is_s3(wav_loc: str) -> (bool, str):
    """
    Check if the wav_loc is an s3 bucket
    :param wav_loc:
        The wav_loc to check
    :return:
        A tuple of (is_s3, bucket_core)
    """

    is_s3_match = re.match(r'^s3://', wav_loc)
    # the bucket name will optionally have a * at the end
    # keep only the bucket name before the *
    bucket_core = re.sub(r'\*$', '', wav_loc)
    bucket_core = re.sub(r'^s3://', '', bucket_core)
    return is_s3_match, bucket_core