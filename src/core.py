import tomllib


def get_creds() -> dict:
    with open("cred.toml", "rb") as f:  # tomllib requires binary mode
        data = tomllib.load(f)
    return data


CREDS = get_creds()
