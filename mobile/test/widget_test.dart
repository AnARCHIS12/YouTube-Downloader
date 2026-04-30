import 'package:flutter_test/flutter_test.dart';

import 'package:youtube_downloader_mobile/main.dart';

void main() {
  testWidgets('shows downloader controls', (WidgetTester tester) async {
    await tester.pumpWidget(const YouTubeDownloaderApp());

    expect(find.text('YouTube Downloader'), findsOneWidget);
    expect(find.text('Telecharger'), findsOneWidget);
    expect(find.text('Activite'), findsOneWidget);
  });

  testWidgets('asks for a url before preview download', (WidgetTester tester) async {
    await tester.pumpWidget(const YouTubeDownloaderApp());

    await tester.tap(find.text('Telecharger'));
    await tester.pump();

    expect(find.text('Colle un lien YouTube avant de lancer.'), findsOneWidget);
  });
}
