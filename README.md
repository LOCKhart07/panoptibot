# Panoptibot
Panoptibot is a Telegram bot to manage Olas services deployed on Propel. Panoptibot can help you monitor, stop and restart your services.

</br>
<p align="center">
  <img width="50%" src="images/panoptibot.jpg">
</p>

## Requirements

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/)

## Prepare the repo

1. Clone the repo:

    ```bash
    git clone git@github.com:dvilelaf/panoptibot.git
    cd panoptibot
    ```

2. Install all deps
    ```bash
    uv sync
    ```

3. Copy the env file:

    ```bash
    cp sample.env .env
    ```

    And fill in the required environment variables.


4. Edit `config.yaml` and add the name of your services and agents.


## Run Panoptibot as a Python script

```bash
make run
```

## Run Panoptibot as a systemd service

1. Install and run:

    ```bash
    make install
    make enable
    make start
    ```

2. Verify it is working:
    ```bash
    make status
    ```

## Useful commands

```bash
make run      # run panoptibot
make format   # format files
make install  # install the service (systemd)
make start    # start the service (systemd)
make stop     # stop the service (systemd)
make logs     # see the service logs (systemd)
make update   # pull the latest version, reinstall and restart the service if needed (systemd)
```