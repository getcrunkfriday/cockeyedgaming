from argparse import ArgumentParser
import json
from typing import List

TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/authorize?" \
                  "client_id={client_id}&" \
                  "redirect_uri={redirect_uri}&" \
                  "response_type=code&" \
                  "scope={scope}"


def generate_auth_url(
    client_id: str,
    scopes: List[str],
    redirect_uri: str = "https://www.crunkybot.io/login/authorized"
):
    return TWITCH_AUTH_URL.format(client_id=client_id, redirect_uri=redirect_uri, scope="+".join(scopes))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--config", help="Location of config file.")
    args = parser.parse_known_args()[0]
    with open(args.config) as f:
        config = json.load(f)
    auth_url = generate_auth_url(
        client_id=config["CRUNKYBOT_CLIENT_ID"],
        scopes=config.get("TWITCH_SCOPES", ["channel_subscriptions"])
    )
    print(f"Twitch Auth URL for {config['TWITCH_NICK']}: {auth_url}")