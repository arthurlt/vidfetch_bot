FROM dart:stable AS build

WORKDIR /app
COPY pubspec.yaml ./
RUN dart pub get

COPY . .
RUN dart pub get --offline
RUN dart compile exe main.dart -o main


FROM alpine:latest

RUN apk --no-cache add yt-dlp

COPY --from=build /runtime/ /
COPY --from=build /app/main /app/

CMD [ "/app/main" ]