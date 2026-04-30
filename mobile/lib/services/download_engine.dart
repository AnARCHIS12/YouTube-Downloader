import 'package:flutter/services.dart';

enum DownloadStatus {
  idle,
  running,
  completed,
  unsupported,
  failed,
}

class DownloadRequest {
  const DownloadRequest({
    required this.url,
    required this.quality,
  });

  final String url;
  final String quality;
}

class DownloadResult {
  const DownloadResult({
    required this.status,
    required this.message,
    required this.progress,
  });

  final DownloadStatus status;
  final String message;
  final double progress;
}

class DownloadEngine {
  DownloadEngine() {
    _channel.setMethodCallHandler(_handleMethodCall);
  }

  static const MethodChannel _channel = MethodChannel(
    'youtube_downloader/downloads',
  );

  void Function(DownloadResult progress)? onProgress;

  Future<String> getDestination() async {
    try {
      return await _channel.invokeMethod<String>('getDestination') ??
          'Telechargements/YouTube Downloader';
    } on MissingPluginException {
      return 'Telechargements/YouTube Downloader';
    }
  }

  Future<String?> chooseDestination() async {
    try {
      return await _channel.invokeMethod<String>('pickDestination');
    } on MissingPluginException {
      return null;
    }
  }

  Future<DownloadResult> start(DownloadRequest request) async {
    try {
      final Map<dynamic, dynamic>? result = await _channel.invokeMapMethod(
        'download',
        <String, String>{
          'url': request.url,
          'quality': request.quality,
        },
      );

      return DownloadResult(
        status: DownloadStatus.completed,
        progress: (result?['progress'] as num?)?.toDouble() ?? 1,
        message:
            result?['message'] as String? ?? 'Telechargement mobile termine.',
      );
    } on MissingPluginException {
      return const DownloadResult(
        status: DownloadStatus.unsupported,
        progress: 0,
        message: 'Le telechargement reel est disponible sur Android.',
      );
    } on PlatformException catch (error) {
      return DownloadResult(
        status: DownloadStatus.failed,
        progress: 0,
        message: error.message ?? 'Erreur pendant le telechargement.',
      );
    }
  }

  Future<void> _handleMethodCall(MethodCall call) async {
    if (call.method != 'downloadProgress') {
      return;
    }

    final Object? rawArguments = call.arguments;
    if (rawArguments is! Map) {
      return;
    }

    onProgress?.call(
      DownloadResult(
        status: DownloadStatus.running,
        progress: (rawArguments['progress'] as num?)?.toDouble() ?? 0,
        message: rawArguments['message'] as String? ?? 'Telechargement...',
      ),
    );
  }
}
