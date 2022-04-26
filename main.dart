import 'dart:async';
import 'dart:io' as io;
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'package:teledart/teledart.dart';
import 'package:teledart/telegram.dart';

Future<void> main() async {
  final envVars = io.Platform.environment;
  final telegram = Telegram(envVars['BOT_TOKEN']!);

  // Requires a custom-patched Bibliogram instance that will export JSON for posts
  final String bibliogramInstance = envVars['CUSTOM_BIBLIOGRAM'] ?? "null";
  final username = (await telegram.getMe()).username;

  // TeleDart uses longpoll by default if no update fetcher is specified.
  var teledart = TeleDart(envVars['BOT_TOKEN']!, Event(username!));

  teledart.start();

  print('Antisocial Vid Bot authenticated as... $username');

  teledart
    .onUrl(RegExp('instagram'))
    .listen((message) async => message.replyVideo(
      await instagramVideo(message.text!), 
      disable_notification: true, 
      withQuote: true,
      caption: await getInstagramTitle(message.text!, bibliogramInstance)));

  teledart
    .onUrl(RegExp('tiktok'))
    .listen((message) async => message.replyVideo(
      await tiktokVideo(message.text!), 
      disable_notification: true, 
      withQuote: true, 
      caption: await getTiktokTitle(message.text!)));

  teledart
    .onUrl(RegExp('redd.?it'))
    .listen((message) async => await getRedditType(message.text!) ?? 
      message.replyVideo(await redditVideo(message.text!),
      disable_notification: true,
      withQuote: true,
      caption: await getRedditTitle(message.text!)));
}

Future<io.File> instagramVideo(String url) async {
  print("received instagram request");
  final String file = '/tmp/video.mp4';
  final result = await io.Process.run(
    'yt-dlp', [url,'--force-overwrites', '-o', file]);
  print(result.stdout);
  return(io.File(file));
}

Future<String> getInstagramTitle(String url, String bibliogramUrl) async {
  if (bibliogramUrl == "null") {
    return "";
  }
  List urlPathSegments = Uri.parse(url).pathSegments;
  var response = await http.get(
    Uri.parse('https://$bibliogramUrl/${urlPathSegments[0]}/json/${urlPathSegments[1]}'));
  var json = jsonDecode(response.body);
  return (json['data']['edge_media_to_caption']['edges'][0]['node']['text'].split('\n')[0]);
}

Future<io.File> tiktokVideo(String url) async {
  print("received tiktok request");
  final String file = '/tmp/video.mp4';
  final result = await io.Process.run(
    'yt-dlp', [url, '--force-overwrites', '-o', file]);
  print(result.stdout);
  return(io.File(file));
}

Future<String> getFullURL(String url) async {
  final curlProcess = await io.Process.run(
    'curl', ['-sL', '-w %{url_effective}', '-o /dev/null', url]);
  return(curlProcess.stdout);
}

Future<String> getTiktokTitle(String url) async {
  final fullUrl = await getFullURL(url);
  var response = await http.get(
    Uri.parse('https://www.tiktok.com/oembed?url=${fullUrl.replaceAll(' ', '')}'));
  var json = jsonDecode(response.body);
  return(json['title']);
}

Future<io.File> redditVideo(String url) async {
  print("received reddit request");
  final String file = '/tmp/video.mp4';
  final result = await io.Process.run(
    'yt-dlp', [url,'--force-overwrites', '-o', file]);
  print(result.stdout);
  return(io.File(file));
}

Future<String> getRedditTitle(String url) async {
  final fullUrl = await getFullURL(url);
  var response = await http.get(
    Uri.parse('${fullUrl.replaceAll(' ', '')}.json'));
  var json = jsonDecode(response.body);
  return(json[0]['data']['children'][0]['data']['title']);
}

Future<bool?> getRedditType(String url) async {
  final fullUrl = await getFullURL(url);
  var response = await http.get(
    Uri.parse('${fullUrl.replaceAll(' ', '')}.json'));
  var json = jsonDecode(response.body);
  print('Post type is: ${json[0]['data']['children'][0]['data']['post_hint']}');
  if (RegExp('video').hasMatch(json[0]['data']['children'][0]['data']['post_hint'])) {
    return null;
  } else {
    return false;
  }
}