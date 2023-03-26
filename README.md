# auto_racer

Automatically enter races every 5 minutes

## Usage

### Setting Up

1. Install the packages with `pip install -r requirements.txt`.
1. Rename the `credentials.example.json` to `credentials.json`.
1. Enter your account credentials, model URL and leaderboard URL (multiple accounts is supported).

> Note: You don't need to do **Step 1** if you're using Docker.

### Normal Usage

1. Run `main.py` with Python (3.11 was used in development).

```bash
python main.py
```

### Docker Container

1. Build the container with `docker build -t auto_racer .`
2. Run the container with `docker run -it -rm --name auto_racer_instance auto_racer`

> Note: If you changed the contents of `credentials.json`, you need to rebuild the Docker image.

## FAQ

1. What is `HTTP Error 429`?

- Since the time between each evaluation is unknown, a good estimate is around 5 minutes. But even then, the evaluation might not be complete yet, and when it sends the request, this error pops up. **You can just ignore it.**

2. Is this illegal

- Dunno, probably not

## Screenshot

![image](https://user-images.githubusercontent.com/20278298/227785442-52283138-e075-42bc-bb3f-38d9421ec460.png)
