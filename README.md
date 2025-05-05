# VidFetch_bot
This bot watches messages for URLs then passes those to yt-dlp for processing and download. It then replies to the message containing the URL with the video embedded.

Supply your bot's API token via environment variable `BOT_TOKEN`.

## TODO:
- [ ] Improve README
- [ ] Add unit tests
- [ ] Rewrite to use `yt-dlp` library
- [ ] Move Docker image build/publish to `workflow.yaml`
