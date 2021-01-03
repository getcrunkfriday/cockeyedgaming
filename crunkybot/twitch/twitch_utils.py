import socket
import re
import requests
import json
import time
from typing import Tuple, Optional, Dict
from crunkybot.twitch.config3 import TWITCH_HOST, TWITCH_PORT, TWITCH_NICK, \
    TWITCH_CHAN, TWITCH_PASS, TWITCH_SUB_PASS

PING_MSG = "PING :tmi.twitch.tv\r\n"
CHAT_MSG=re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")
COMMAND_SYMBOLS = ["!"]
TWITCH_V2_STREAMS_URL = "https://api.twitch.tv/helix/streams"
TWITCH_OAUTH_URL = "https://id.twitch.tv/oauth2/token"

CLIENT_SCOPES = [
    'bits:read',
    'channel:manage:broadcast',
    'channel:manage:extensions',
    'channel:manage:redemptions',
    'channel:read:hype_train',
    'channel:read:redemptions',
    'channel:read:subscriptions',
    'moderation:read',
    'user:read:broadcast'
]

class TwitchSocket:
    def __init__(
        self,
        twitch_host: str,
        twitch_port: int,
        twitch_channel: str,
        twitch_user: str,
        twitch_password: str,
        config: Dict
    ):
        self._host = twitch_host
        self._port = twitch_port
        self._channel = twitch_channel
        self._user = twitch_user
        self._password = twitch_password

        self._client_id = config['CRUNKYBOT_CLIENT_ID']
        self._client_secret = config['CRUNKYBOT_CLIENT_SECRET']
        self._socket = socket.socket()
        self._token = None

    def connect(self):
        self._socket.connect((self._host, self._port))
        self._socket.send("PASS {}\r\n".format(self._password).encode("utf-8"))
        self._socket.send("NICK {}\r\n".format(self._user).encode("utf-8"))
        self._socket.send("JOIN #{}\r\n".format(self._channel).encode("utf-8"))

    def receive(self):
        response = self._socket.recv(1024).decode("utf-8")
        if response == PING_MSG:
            self._socket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
        return response

    def send(self, msg):
        self._socket.send(msg.encode("utf-8"))

    def get_token(self):
        token_time_left = self._get_token_time()
        if self._token is None or token_time_left <= 0:
            data = {
                'client_id': self._client_id,
                'client_secret': self._client_secret,
                'grant_type': 'client_credentials',
                'scope': ' '.join(CLIENT_SCOPES)
            }
            response = requests.post(
                TWITCH_OAUTH_URL,
                data = data
            )
            assert response.status_code == 200, f"Failed to retrieve client token. Response {response}."
            token = json.loads(response.text)
            self._token = {
                'client_id': self._client_id,
                'token': token['access_token'],
                'time_started': int(time.time()),
                'expires_in': token['expires_in']
            }
        return self._token

    def _get_token_time(self):
        if self._token is None:
            return 0
        time_elapsed = int(time.time()) - self._token['time_started']
        return self._token['expires_in'] - time_elapsed


def connect(config: Dict) -> TwitchSocket:
    twitch_socket = TwitchSocket(
        config[TWITCH_HOST],
        config[TWITCH_PORT],
        config[TWITCH_CHAN],
        config[TWITCH_NICK],
        config[TWITCH_PASS],
        config
    )
    twitch_socket.connect()
    return twitch_socket

def get_username(twitch_msg: str) -> str:
    return re.search(r"\w+", twitch_msg).group(0)

def get_message(twitch_msg: str) -> Tuple[Optional[str], str]:
    message = CHAT_MSG.sub("", twitch_msg).strip()
    command = message.split()[0]
    if command[0] not in COMMAND_SYMBOLS:
        command = None
    else:
        command = command[1:]
    return command, message

def get_twitch_headers(twitch_socket: TwitchSocket) -> Dict:
    token = twitch_socket.get_token()
    return {
        "Client-ID": token['client_id'],
        "Authorization": f"Bearer {token['token']}"
    }

def send_message(
    twitch_socket: TwitchSocket,
    channel: str,
    user: str,
    msg: str,
    debug=False
):
    msg=msg.replace("${username}",user)
    if not debug:
        twitch_socket.send("PRIVMSG #{} :{}\r\n".format(channel, msg))
    else:
        print(msg)

# Utilities for getting information from Twitch API
def uptime(twitch_socket: TwitchSocket, config: Dict):
    try:
        twitch_url = TWITCH_V2_STREAMS_URL
        request = requests.get(
            TWITCH_V2_STREAMS_URL,
            headers=get_twitch_headers(twitch_socket),
            params={
                "user_login": config[TWITCH_CHAN]
            }
        )
        json_dict = json.loads(request.text)["data"]
        if len("data") > 0 in json_dict and json_dict['data'][0]['type'] == 'live':
            timestamp = json_dict['data'][0]['started_at']
            dt_timestamp = datetime.datetime.strptime(
                timestamp, '%Y-%m-%dT%H:%M:%SZ'
            )
            now = datetime.datetime.utcnow()
            diff = now - dt_timestamp
            diff_str = str(diff).split(",")
            time_idx = 0
            live_str = ""
            if len(diff_str) > 1:
                live_str = diff_str[0]+", "
                time_idx = 1
            hours = diff_str[time_idx].split(":")
            live_str += f"{hours[0]} hours and {int(hours[1])} minutes."
            print(live_str)
            send_message(
                twitch_socket,
                config[TWITCH_CHAN],
                "crunkybot",
                f"Stream has been live for {live_str}"
            )
            # "2017-08-14T15:45:17Z"
        else:
            send_message(
                twitch_socket,
                config[TWITCH_CHAN],
                "crunkybot",
                "The stream isn't live :(."
            )
    except Exception as e:
        print(f"Error in {e}")
