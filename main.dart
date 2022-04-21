import 'dart:async';
import 'dart:io' as io;
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'package:teledart/teledart.dart';
import 'package:teledart/telegram.dart';

Future<void> main() async {
  final envVars = io.Platform.environment;
  var telegram = Telegram(envVars['BOT_TOKEN']!);
  final username = (await telegram.getMe()).username;

  // TeleDart uses longpoll by default if no update fetcher is specified.
  var teledart = TeleDart(envVars['BOT_TOKEN']!, Event(username!));

  teledart.start();

  print('Antisocial Vid Bot authenticated as... $username');

  teledart
    .onUrl(RegExp('instagram'))
    .listen((message) async => message.replyVideo(
      await instagramVideo(message.text ?? null.toString()), 
      disable_notification: true, 
      withQuote: true));

  teledart
    .onUrl(RegExp('tiktok'))
    .listen((message) async => message.replyVideo(
      await tiktokVideo(message.text ?? null.toString()), 
      disable_notification: true, 
      withQuote: true, 
      caption: await getTiktokTitle(message.text ?? null.toString())));
}

Future<dynamic> instagramVideo(String url) async {
  print("received instagram request");
  final String file = 'instagram_video.mp4';
  final result = await io.Process.run('yt-dlp', [url,'--force-overwrites', '-o', file]);
  print(result.stdout);
  return(io.File(file));
}

Future<dynamic> tiktokVideo(String url) async {
  print("received tiktok request");
  final String file = 'tiktok_video.mp4';
  final result = await io.Process.run('yt-dlp', [url, '--force-overwrites', '-o', file]);
  print(result.stdout);
  return(io.File(file));
}

Future<String> getFullTiktokUrl(String url) async {
  final curlProcess = await io.Process.run('curl', ['-sL', '-w %{url_effective}', '-o /dev/null', url]);
  return(curlProcess.stdout);
}

Future<String> getTiktokTitle(String url) async {
  final fullUrl = await getFullTiktokUrl(url);
  var response = await http.get(Uri.parse('https://www.tiktok.com/oembed?url=${fullUrl.replaceAll(' ', '')}'));
  var json = jsonDecode(response.body);
  return(json['title']);
}