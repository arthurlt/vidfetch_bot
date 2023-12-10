import 'dart:async';
import 'dart:io' as io;
import 'dart:convert';

import 'package:teledart/telegram.dart';
import 'package:teledart/teledart.dart';
import 'package:teledart/model.dart';

enum ytDlpFile { video, thumbnail, json }

Future<void> main() async {
  const String tokenEnvVar = 'BOT_TOKEN';
  final Map<String, String?> envVars = io.Platform.environment;
  late String botToken;

  if (validateString(envVars[tokenEnvVar])) {
    botToken = envVars[tokenEnvVar]!;
  } else {
    throw 'No bot token provided!! Make sure $tokenEnvVar is properly set as an environment variable.';
  }

  final String? username = (await Telegram(botToken).getMe()).username;
  // TeleDart uses longpoll by default if no update fetcher is specified.
  var teledart = TeleDart(botToken, Event(username!));

  teledart.start();

  print('Antisocial Vid Bot authenticated as... $username');

  teledart
      .onMessage(entityType: 'url')
      .listen((message) => processMessage(message));
}

bool validateString(final String? string) {
  return string?.isNotEmpty ?? false;
}

Future<void> processMessage(final TeleDartMessage message) async {
  if (!validateString(message.text)) {
    message.reply(
        'Error, your message appears to be empty?? \n Something has gone wrong.',
        withQuote: true);
    return;
  }

  final RegExp urlRegex = RegExp(
      r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()!@:%_\+.~#?&\/\/=]*)');
  final Iterable<Match> urlMatches = urlRegex.allMatches(message.text!);

  print(
      'found ${urlMatches.length} URL(s) from ${message.from?.username} in ${message.chat.title}');
  for (final Match urlMatch in urlMatches) {
    final String url = urlMatch[0]!;
    final String downloadDir =
        '/tmp/yt-dlp-${message.messageId}-${urlMatch.hashCode}';
    print(url);

    // Testing if yt-dlp can process the video
    // TODO: implement way to sendChatAction while processing & downloading
    final io.ProcessResult simulateResult = await runYtDlp(url, simulate: true);
    if (simulateResult.exitCode != 0) {
      print('yt-dlp failed to process $url\n${simulateResult.stderr}');
      continue;
    }
    // Using yt-dlp to download the video
    final io.ProcessResult downloadResult = await runYtDlp(url, dir: downloadDir);
    if (downloadResult.exitCode != 0) {
      print('yt-dlp failed to download $url\n${downloadResult.stderr}');
      continue;
    }
    // TODO: make sure these files exist
    // TODO: make sure the video files is under 50mb
    final Map<ytDlpFile, io.File> files = {
      ytDlpFile.video: io.File('$downloadDir/video.mp4'),
      ytDlpFile.thumbnail: io.File('$downloadDir/video.jpg'),
      ytDlpFile.json: io.File('$downloadDir/video.info.json')
    };
    final Map videoInfo = jsonDecode(files[ytDlpFile.json]!.readAsStringSync());

    await message.replyVideo(files[ytDlpFile.video],
      duration: (videoInfo['duration']).round(),
      width: videoInfo['width'],
      height: videoInfo['height'],
      caption: generateCaption(videoInfo),
      //thumbnail: files[ytDlpFile.thumbnail],
      thumbnail: videoInfo['thumbnail'],
      withQuote: true);

    io.Directory(downloadDir).deleteSync(recursive: true);
  }
}

// Provide with a json decoded Map of the yt-dlp info.json file
// TODO: remove hashtags in caption
String generateCaption(final Map info) {
  final RegExp regex = RegExp(r'#\w+\s*');
  final String caption;
  if (!validateString(info['description'])) {
    caption = info['title'];
  } else {
    caption = info['description'];
  }
  return caption.replaceAll(regex, '');
}

// TODO: extend ProcessResult class to return some more data
Future<io.ProcessResult> runYtDlp(final String videoUrl,
    {final bool simulate = false, String dir = '/tmp'}) {
  List<String> args = [
    '--write-info-json',
    //format conversion is failing https://github.com/yt-dlp/yt-dlp/issues/6866
    //'--write-thumbnail',
    //'--convert-thumbnails',
    //'jpg',
    '--remux-video',
    'mp4',
    '--output',
    'video.%(ext)s',
    videoUrl
  ];

  if (simulate) {
    args = args + ['--simulate'];
  }

  if (!io.Directory(dir).existsSync()) {
    try {
      io.Directory(dir).createSync(recursive: true);
    } catch (e) {
      print('Exception details:\n $e');
      print('Setting dir to /tmp as fallback');
      dir = '/tmp';
    }
  }

  return io.Process.run('yt-dlp', args, workingDirectory: dir);
}
