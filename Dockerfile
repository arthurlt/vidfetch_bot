FROM dart:stable AS build

WORKDIR /app
COPY pubspec.yaml ./
RUN dart pub get

COPY . .
RUN dart pub get --offline
RUN dart compile exe main.dart -o main


FROM debian:stable-slim

RUN apt-get update && apt-get install -y \
	curl \
	python3 \
	ffmpeg \
	python3-mutagen \
	python3-websockets \
	python3-brotli \
	atomicparsley \
	&& rm -rf /var/lib/apt/lists/* 
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp && chmod a+rx /usr/local/bin/yt-dlp
COPY --from=build /runtime/ /
COPY --from=build /app/main /app/

CMD [ "/app/main" ]