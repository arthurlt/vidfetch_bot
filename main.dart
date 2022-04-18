import 'dart:async';
import 'dart:io' as io;
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'package:teledart/model.dart';
import 'package:teledart/teledart.dart';
import 'package:teledart/telegram.dart';

Future<void> main() async {
  final envVars = io.Platform.environment;
  var telegram = Telegram(envVars['BOT_TOKEN']!);
  final username = (await telegram.getMe()).username;

  // TeleDart uses longpoll by default if no update fetcher is specified.
  var teledart = TeleDart(envVars['BOT_TOKEN']!, Event(username!));

  teledart.start();

  teledart
    .onCommand('list')
    .listen((message) async => message.reply("<pre>${await listDir()}</pre>", parse_mode: 'HTML'));

  teledart
    .onUrl(RegExp('instagram'))
    .listen((message) async => message.replyVideo(await instagramVideo(message.text ?? null.toString()), disable_notification: true));

  teledart
    .onUrl(RegExp('tiktok'))
    .listen((message) async => message.replyVideo(await tiktokVideo(message.text ?? null.toString()), disable_notification: true, caption: await getTiktokTitle(message.text ?? null.toString())));
  // You can even filter streams with stream processing methods
  // See: https://www.dartlang.org/tutorials/language/streams#methods-that-modify-a-stream
  teledart
      .onMessage(keyword: 'dart')
      .where((message) => message.text?.contains('telegram') ?? false)
      .listen((message) => message.replyPhoto(
          //  io.File('example/dash_paper_plane.png'),
          'https://raw.githubusercontent.com/DinoLeung/TeleDart/master/example/dash_paper_plane.png',
          caption: 'This is how Dash found the paper plane'));

  // Inline mode.
  teledart.onInlineQuery().listen((inlineQuery) => inlineQuery.answer([
        InlineQueryResultArticle(
            id: 'ping',
            title: 'ping',
            input_message_content: InputTextMessageContent(
                message_text: '*pong*', parse_mode: 'MarkdownV2')),
        InlineQueryResultArticle(
            id: 'ding',
            title: 'ding',
            input_message_content: InputTextMessageContent(
                message_text: '*_dong_*', parse_mode: 'MarkdownV2')),
      ]));
}

Future<String> listDir() async {
  io.Process process = await io.Process.start('ls', ['-l']);
  // Wait for hte process to finish; get the exit code.
  final results = await process.stdout.transform(io.systemEncoding.decoder).join();
  return(results);
}

Future<dynamic> instagramVideo(String url) async {
  print("received instagram request");
  final String file = 'instagram_video.mp4';
  final result = await io.Process.run('yt-dlp', [url,'--force-overwrites' ,'-o', file]);
  print(result.stdout);
  return(io.File(file));
}

Future<dynamic> tiktokVideo(String url) async {
  print("received tiktok request");
  final String file = 'tiktok_video.mp4';
  final fullUrl = await getFullTiktokUrl(url);
  final result = await io.Process.run('yt-dlp', [fullUrl, '--force-overwrites', '-o', file]);
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