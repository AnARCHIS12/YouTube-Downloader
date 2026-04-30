import 'package:flutter/material.dart';

import 'services/download_engine.dart';

void main() {
  runApp(const YouTubeDownloaderApp());
}

class YouTubeDownloaderApp extends StatelessWidget {
  const YouTubeDownloaderApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'YouTube Downloader',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFFF0033),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF09090B),
        useMaterial3: true,
      ),
      home: const DownloaderHomePage(),
    );
  }
}

class DownloaderHomePage extends StatefulWidget {
  const DownloaderHomePage({super.key});

  @override
  State<DownloaderHomePage> createState() => _DownloaderHomePageState();
}

class _DownloaderHomePageState extends State<DownloaderHomePage> {
  final TextEditingController _urlController = TextEditingController();
  final DownloadEngine _downloadEngine = DownloadEngine();
  final List<String> _qualities = <String>[
    '360p',
    '480p',
    '720p',
    '1080p',
    '1440p',
    '2160p',
    'Audio',
  ];

  String _quality = '1080p';
  String _activity = 'En attente d\'un lien.';
  String _destination = 'Telechargements/YouTube Downloader';
  double _progress = 0;
  bool _isPreparing = false;

  @override
  void initState() {
    super.initState();
    _loadDestination();
  }

  @override
  void dispose() {
    _downloadEngine.onProgress = null;
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _loadDestination() async {
    final String destination = await _downloadEngine.getDestination();
    if (!mounted) {
      return;
    }

    setState(() => _destination = destination);
  }

  Future<void> _chooseDestination() async {
    final String? destination = await _downloadEngine.chooseDestination();
    if (!mounted || destination == null) {
      return;
    }

    setState(() {
      _destination = destination;
      _activity = 'Dossier de sortie selectionne.';
    });
  }

  Future<void> _startDownloadPreview() async {
    final String url = _urlController.text.trim();
    if (url.isEmpty) {
      setState(() {
        _activity = 'Colle un lien YouTube avant de lancer.';
        _progress = 0;
      });
      return;
    }

    setState(() {
      _isPreparing = true;
      _activity = 'Preparation du telechargement...';
      _progress = 0.08;
    });

    _downloadEngine.onProgress = (DownloadResult progress) {
      if (!mounted) {
        return;
      }

      setState(() {
        _activity = progress.message;
        _progress = progress.progress;
      });
    };

    final DownloadResult result = await _downloadEngine.start(
      DownloadRequest(url: url, quality: _quality),
    );

    if (!mounted) {
      return;
    }

    setState(() {
      _isPreparing = false;
      _activity = result.message;
      _progress = result.progress;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 22, 20, 28),
          children: <Widget>[
            const _AppHeader(),
            const SizedBox(height: 28),
            Text(
              'Telecharge tes videos avec une interface mobile simple.',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.w800,
                    height: 1.08,
                  ),
            ),
            const SizedBox(height: 22),
            _Panel(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  TextField(
                    controller: _urlController,
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      hintText: 'Coller un lien YouTube',
                      hintStyle: const TextStyle(color: Color(0xFF8D93A1)),
                      filled: true,
                      fillColor: const Color(0xFF0F1014),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: const BorderSide(color: Color(0xFF2B2C34)),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: const BorderSide(color: Color(0xFF2B2C34)),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: const BorderSide(color: Color(0xFFFF0033)),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    initialValue: _quality,
                    dropdownColor: const Color(0xFF151519),
                    decoration: InputDecoration(
                      labelText: 'Qualite',
                      labelStyle: const TextStyle(color: Color(0xFFB6BCC8)),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    items: _qualities
                        .map(
                          (String quality) => DropdownMenuItem<String>(
                            value: quality,
                            child: Text(quality),
                          ),
                        )
                        .toList(),
                    onChanged: (String? value) {
                      if (value != null) {
                        setState(() => _quality = value);
                      }
                    },
                  ),
                  const SizedBox(height: 16),
                  OutlinedButton(
                    onPressed: _isPreparing ? null : _chooseDestination,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.white,
                      side: const BorderSide(color: Color(0xFF3A3C45)),
                      minimumSize: const Size.fromHeight(48),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: const Text('Choisir le dossier de sortie'),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    _destination,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Color(0xFFB6BCC8),
                      fontSize: 13,
                    ),
                  ),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: _isPreparing ? null : _startDownloadPreview,
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFFFF0033),
                      foregroundColor: Colors.white,
                      minimumSize: const Size.fromHeight(50),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: Text(
                      _isPreparing ? 'Preparation...' : 'Telecharger',
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 18),
            _Panel(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const Text(
                    'Activite',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w800,
                      fontSize: 18,
                    ),
                  ),
                  const SizedBox(height: 14),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(999),
                    child: LinearProgressIndicator(
                      value: _progress,
                      minHeight: 10,
                      backgroundColor: const Color(0xFF292A31),
                      valueColor: const AlwaysStoppedAnimation<Color>(
                        Color(0xFFFF0033),
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Text(
                    _activity,
                    style: const TextStyle(color: Color(0xFFB6BCC8)),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AppHeader extends StatelessWidget {
  const _AppHeader();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: const Color(0xFFFF0033),
            borderRadius: BorderRadius.circular(8),
          ),
          clipBehavior: Clip.antiAlias,
          child: Image.asset(
            'assets/youtube-logo.png',
            fit: BoxFit.cover,
          ),
        ),
        const SizedBox(width: 14),
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'YouTube Downloader',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                ),
              ),
              SizedBox(height: 3),
              Text(
                'Android avec yt-dlp integre',
                style: TextStyle(color: Color(0xFFB6BCC8)),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _Panel extends StatelessWidget {
  const _Panel({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF151519),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFF2B2C34)),
      ),
      child: child,
    );
  }
}
