import json
import os
from argparse import ArgumentParser
from time import sleep
import requests

from typing import Dict

TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/token"
                  # "?client_id={client_id}" \
                  # "client_secret={client_secret}" \
                  # "code={code}>&" \
                  # "grant_type=authorization_code&" \
                  # "redirect_uri={redirect_uri}"


def make_token_file(
    channel_id: str,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str = "https://www.crunkybot.io/login/authorized",
    output_dir: str = "/tmp/crunkybot_tokens/",
    is_refresh:bool = False
) -> Dict:
    #  {"access_token":"qw4fn0u6xfnfghv78c10yx3cxtfutj",
    #  "expires_in":15724,
    #  "refresh_token":"h1imrw8zv66p4fbiqbw03b6zcbsvu8pn6rfp0k8vgaq9yrzkvi",
    #  "scope":["bits:read","channel:manage:broadcast","channel:manage:extensions","channel:manage:redemptions"],
    #  "token_type":"bearer"}
    os.makedirs(output_dir, exist_ok=True)
    token_file = os.path.join(output_dir, f"{channel_id}.json")
    if is_refresh:
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': code,
            'redirect_uri': redirect_uri
        }
    else:
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri
        }
    response = requests.post(TWITCH_AUTH_URL, data=data)
    response_json = json.loads(response.text)
    with open(token_file, 'w') as f:
        json.dump(response_json, f)
    return response.text


def run_server(
    seed_token: str,
    config: Dict,
    redirect_url: str = "https://www.crunkybot.io/login/authorized",
    output_dir: str = "/tmp/crunkybot_tokens/",
    sleep_time: int = 900  # 15 minutes
):
    os.makedirs(output_dir, exist_ok=True)
    channel_id = config["TWITCH_CHAN"]
    client_id = config["CRUNKYBOT_CLIENT_ID"]
    client_secret = config["CRUNKYBOT_CLIENT_SECRET"]
    print(f"Making seed token file from code {seed_token}...")
    new_token = make_token_file(channel_id, client_id, client_secret, seed_token, redirect_url)
    print(f"Received token {new_token}...")
    sleep(sleep_time)
    while True:
        with open(os.path.join(output_dir, f"{channel_id}.json")) as f:
            token = json.load(f)
        print(f"Making new token from refresh token {token}...")
        new_token = make_token_file(
            channel_id, client_id, client_secret, token["refresh_token"], redirect_url, is_refresh=True
        )
        print(f"Received token {new_token}...")
        sleep(sleep_time)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--config", type=str, required=True, help="Location of config file.")
    parser.add_argument("--auth_code", type=str, required=True, help="Seed auth code from `generate_auth_url`.")
    args = parser.parse_known_args()[0]
    with open(args.config) as f:
        config = json.load(f)

    run_server(args.auth_code, config, sleep_time=900)
