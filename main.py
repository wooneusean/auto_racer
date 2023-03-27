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


def time_format(time):
    result = time / 1000 / 60
    if result < 0:
        result * 60
    return round(result, 3)


def cognito_login(username, password):
    print(f'[{datetime.datetime.now()}] {username[:16]} > Attempting to log in...')
    aws = AWSSRP(
        pool_id='us-east-1_UoORhSEJc',
        username=username,
        password=password,
        pool_region='us-east-1',
        client_id='2c58a2ujl9u8d1sfcsktb2ik4v'
    )
    result = aws.authenticate_user()
    return {'token': result['AuthenticationResult']['IdToken'], 'expiry': int(round(time.time())) + int(result['AuthenticationResult']['ExpiresIn'])}


tokens = {}


def get_latest_user_submission(token, leaderboard_arn):
    data = {"LeaderboardArn": leaderboard_arn}
    encoded_data = json.dumps(data).encode()
    req = request.Request(
        'https://api-proxy.prod.deepracer.com/getLatestUserSubmission',
        data=encoded_data,
        headers={
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0",
            'Content-Type': 'text/plain;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'Content-Length': len(encoded_data)
        }
    )
    return json.loads(request.urlopen(req).read().decode())['LeaderboardSubmission']


def get_ranked_user_submission(token, leaderboard_arn):
    data = {"LeaderboardArn": leaderboard_arn}
    encoded_data = json.dumps(data).encode()
    req = request.Request(
        'https://api-proxy.prod.deepracer.com/getRankedUserSubmission',
        data=encoded_data,
        headers={
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0",
            'Content-Type': 'text/plain;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'Content-Length': len(encoded_data)
        }
    )
    return json.loads(request.urlopen(req).read().decode())['LeaderboardSubmission']


def submit(p, model_arn, leaderboard_arn):
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
            'authorization': f'Bearer {tokens[p["username"]]["token"]}',
            'Content-Length': len(encoded_data)
        }
    )
    try:
        request.urlopen(req)
        print(
            f'[{datetime.datetime.now()}] {p["username"][:16]} > Successfully started race!'
        )
    except HTTPError as e:
        print(f'[{datetime.datetime.now()}] {p["username"][:16]} > {str(e)}')


def start_race(scheduler):
    global tokens

    here = os.path.dirname(os.path.abspath(__file__))
    f = open(os.path.join(here, 'credentials.json'))
    profiles = json.load(f)
    f.close()

    scheduler.enter(60 * 5, 1, start_race, (scheduler,))

    for p in profiles:
        if (p['username'] not in tokens) or ((int(round(time.time())) + 60) >= tokens[p['username']]['expiry']):
            try:
                tokens[p['username']] = cognito_login(
                    p['username'], p['password']
                )
            except Exception as e:
                print(
                    f'[{datetime.datetime.now()}] {p["username"][:16]} > {str(e)}'
                )
                continue

        model_arn = unquote(p['model_url'].split('/')[-1])
        leaderboard_arn = unquote(p['leaderboard_url'].split('/')[-1])

        latest_submission = get_latest_user_submission(
            tokens[p['username']]['token'],
            leaderboard_arn
        )

        # Get latest submission data
        latest_status = latest_submission['LeaderboardSubmissionStatusType']
        model_name = latest_submission['ModelName']

        # Get ranked submission data
        ranked_submission = get_ranked_user_submission(
            tokens[p['username']]['token'],
            leaderboard_arn
        )
        ranked_total_time = time_format(ranked_submission['TotalLapTime'])
        ranked_model_name = ranked_submission['ModelName']

        if latest_status == 'SUCCESS':
            total_time = time_format(latest_submission['TotalLapTime'])

            print(
                f'[{datetime.datetime.now()}] {p["username"][:16]} > Previous submission is done.\n' +
                f'[{datetime.datetime.now()}] {p["username"][:16]} > Results: {model_name} -> {total_time}. Best: {ranked_model_name} -> {ranked_total_time}.'
            )
            submit(p, model_arn, leaderboard_arn)
        elif latest_status == 'QUEUED' or latest_status == 'RUNNING':
            print(
                f'[{datetime.datetime.now()}] {p["username"][:16]} > Previous submission is still ongoing, skipping for now.'
            )
        else:
            print(
                f'[{datetime.datetime.now()}] {p["username"][:16]} > Something happened to the previous submission, not successful, queued or running.'
            )


# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True
race_scheduler = sched.scheduler(time.time, time.sleep)
race_scheduler.enter(0, 1, start_race, (race_scheduler,))
race_scheduler.run()
