import datetime
import json
import logging
import os
import sched
import time
from urllib import request
from urllib.error import HTTPError
from urllib.parse import unquote

from cognito_idp import AWSSRP, init_make_request_hook

init_make_request_hook()


def cognito_login(username, password):
    print(f'[{datetime.datetime.now()}] {username} > Attempting to log in...')
    aws = AWSSRP(
        pool_id='us-east-1_UoORhSEJc',
        username=username,
        password=password,
        pool_region='us-east-1',
        client_id='2c58a2ujl9u8d1sfcsktb2ik4v'
    )
    tokens = aws.authenticate_user()
    return tokens['AuthenticationResult']['IdToken']


tokens = {}


def start_race(scheduler):
    global tokens

    here = os.path.dirname(os.path.abspath(__file__))
    f = open(os.path.join(here, 'credentials.json'))
    profiles = json.load(f)
    f.close()

    scheduler.enter(60 * 5, 1, start_race, (scheduler,))

    for p in profiles:
        if p['username'] not in tokens:
            try:
                tokens[p['username']] = cognito_login(
                    p['username'], p['password']
                )
            except Exception as e:
                print(
                    f'[{datetime.datetime.now()}] {p["username"]} > {str(e)}')
                continue

        model_arn = unquote(p['model_url'].split('/')[-1])
        leaderboard_arn = unquote(p['leaderboard_url'].split('/')[-1])

        data = json.loads(
            '{"LeaderboardArn":"' +
            leaderboard_arn +
            '","ModelArn":"' +
            model_arn +
            '","TermsAccepted":true,"CompetitionCountryCode":null}'
        )

        encoded_data = json.dumps(data).encode()

        req = request.Request(
            'https://api-proxy.prod.deepracer.com/submit',
            data=encoded_data,
            headers={
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0",
                'Content-Type': 'text/plain;charset=UTF-8',
                'authorization': f'Bearer {tokens[p["username"]]}',
                'Content-Length': len(encoded_data)
            }
        )
        try:
            request.urlopen(req)
            print(
                f'[{datetime.datetime.now()}] {p["username"]} > Successfully started race!'
            )
        except HTTPError as e:
            if e.code == 401 or e.code == 403:
                tokens[p['username']] = cognito_login(
                    p['username'], p['password']
                )
                req = request.Request(
                    'https://api-proxy.prod.deepracer.com/submit',
                    data=encoded_data,
                    headers={
                        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0",
                        'Content-Type': 'text/plain;charset=UTF-8',
                        'authorization': f'Bearer {tokens[p["username"]]}',
                        'Content-Length': len(encoded_data)
                    }
                )
                try:
                    request.urlopen(req)
                    print(
                        f'[{datetime.datetime.now()}] {p["username"]} > Successfully started race!'
                    )
                except HTTPError as e_inner:
                    print(
                        f'[{datetime.datetime.now()}] {p["username"]} > {str(e_inner)}'
                    )
            else:
                print(f'[{datetime.datetime.now()}] {p["username"]} > {str(e)}')


# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True


race_scheduler = sched.scheduler(time.time, time.sleep)
race_scheduler.enter(0, 1, start_race, (race_scheduler,))
race_scheduler.run()
