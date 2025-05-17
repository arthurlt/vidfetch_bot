# VidFetch_Bot

Are you sick of your friends sending you links to TikTok, Instagram, and YouTube only to have to navigate the maze of app download and account signup redirects and popups?

Just add this bot to your group's Telegram meme chat. (Or if they're using a better messaging service just DM the bot the links.)

## How to run

Examples of how to run the bot

### Docker

**TODO**

### Quadlet

If the system you're wanting to run on has Podman>=5 installed you can use [Quadlets](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html). Create a file `vidfetch-bot.container` and place it in `/etc/containers/systemd/`.

```ini
[Unit]
Description=A Telegram bot

[Container]
Image=ghcr.io/arthurlt/vidfetch_bot:latest
Environment="BOT_TOKEN=<INSERT_YOUR_BOT_TOKEN_HERE>"
Pull=newer
#AutoUpdate=registry

[Service]
Restart=always
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target default.target
```

### Kubernetes

**TODO**

### systemd

**TODO**


## Develop

Supply your bot's API token via environment variable `BOT_TOKEN`.

### TODO:
- [ ] Improve README
- [ ] Add/improve docstrings
- [ ] Add unit tests
- [x] Rewrite to use `yt-dlp` as library
- [ ] Move Docker image build/publish to `workflow.yaml`
- [ ] Enable 'strict' checking for `pyright` (unsure how to handle `yt-dlp`)
