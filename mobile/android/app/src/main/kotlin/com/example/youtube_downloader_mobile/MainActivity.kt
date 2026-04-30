package com.anarchis12.youtubedownloader

import android.app.Activity
import android.content.ContentValues
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.provider.DocumentsContract
import android.provider.MediaStore
import com.yausername.ffmpeg.FFmpeg
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLRequest
import com.yausername.youtubedl_android.YoutubeDLException
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.embedding.android.FlutterActivity
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream

class MainActivity : FlutterActivity() {
    private val destinationRequestCode = 4201
    private val mainHandler = Handler(Looper.getMainLooper())
    private var initialized = false
    private var pendingDestinationResult: MethodChannel.Result? = null
    private lateinit var downloadChannel: MethodChannel

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        downloadChannel = MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            "youtube_downloader/downloads"
        )
        downloadChannel.setMethodCallHandler { call, result ->
            when (call.method) {
                "download" -> startDownload(call, result)
                "getDestination" -> result.success(destinationLabel())
                "pickDestination" -> pickDestination(result)
                else -> result.notImplemented()
            }
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)

        if (requestCode != destinationRequestCode) {
            return
        }

        val result = pendingDestinationResult
        pendingDestinationResult = null

        val uri = data?.data
        if (resultCode != Activity.RESULT_OK || uri == null) {
            result?.success(null)
            return
        }

        contentResolver.takePersistableUriPermission(
            uri,
            Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION
        )
        preferences().edit()
            .putString("destination_uri", uri.toString())
            .putString("destination_label", readableName(uri))
            .apply()

        result?.success(destinationLabel())
    }

    private fun pickDestination(result: MethodChannel.Result) {
        if (pendingDestinationResult != null) {
            result.error("destination_busy", "Selection de dossier deja ouverte.", null)
            return
        }

        pendingDestinationResult = result
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE).apply {
            addFlags(
                Intent.FLAG_GRANT_READ_URI_PERMISSION or
                    Intent.FLAG_GRANT_WRITE_URI_PERMISSION or
                    Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or
                    Intent.FLAG_GRANT_PREFIX_URI_PERMISSION
            )
        }
        startActivityForResult(intent, destinationRequestCode)
    }

    private fun startDownload(call: MethodCall, result: MethodChannel.Result) {
        val url = call.argument<String>("url")?.trim().orEmpty()
        val quality = call.argument<String>("quality") ?: "1080p"

        if (url.isEmpty()) {
            result.error("missing_url", "Aucune URL fournie.", null)
            return
        }

        Thread {
            try {
                initializeDownloader()
                updateYoutubeDlIfPossible()

                val workingDir = File(
                    getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS),
                    "YouTube Downloader"
                )
                workingDir.mkdirs()
                val filesBeforeDownload = workingDir.listFiles()?.map { it.absolutePath }?.toSet().orEmpty()

                val request = YoutubeDLRequest(url)
                request.addOption("--no-playlist")
                request.addOption("--newline")
                request.addOption("-o", "${workingDir.absolutePath}/%(title)s.%(ext)s")
                addFormatOptions(request, quality)

                sendProgress(3.0f, -1, "Initialisation de yt-dlp...")

                val response = YoutubeDL.getInstance().execute(request) { progress, etaInSeconds, line ->
                    sendProgress(progress, etaInSeconds, line.ifBlank { "Telechargement en cours..." })
                }
                val publishedFiles = publishCompletedFiles(workingDir, filesBeforeDownload)
                val destination = destinationLabel()
                val publishedMessage = if (publishedFiles.isEmpty()) {
                    "Telechargement termine dans ${workingDir.absolutePath}"
                } else {
                    "Telechargement termine dans $destination"
                }

                mainHandler.post {
                    result.success(
                        mapOf(
                            "message" to publishedMessage,
                            "progress" to 1.0,
                            "outputDir" to destination,
                            "files" to publishedFiles,
                            "output" to response.out
                        )
                    )
                }
            } catch (error: YoutubeDLException) {
                mainHandler.post {
                    result.error(
                        "ytdlp_error",
                        error.message ?: "Erreur yt-dlp.",
                        error.toString()
                    )
                }
            } catch (error: Exception) {
                mainHandler.post {
                    result.error(
                        "download_error",
                        error.message ?: "Erreur de telechargement.",
                        error.toString()
                    )
                }
            }
        }.start()
    }

    @Synchronized
    private fun initializeDownloader() {
        if (initialized) {
            return
        }

        YoutubeDL.getInstance().init(applicationContext)
        FFmpeg.getInstance().init(applicationContext)
        initialized = true
    }

    private fun updateYoutubeDlIfPossible() {
        try {
            sendProgress(2.0f, -1, "Mise a jour de yt-dlp...")
            YoutubeDL.getInstance().updateYoutubeDL(
                applicationContext,
                YoutubeDL.UpdateChannel.STABLE
            )
        } catch (_: Exception) {
            sendProgress(2.0f, -1, "Mise a jour yt-dlp impossible, essai avec la version incluse...")
        }
    }

    private fun addFormatOptions(request: YoutubeDLRequest, quality: String) {
        if (quality == "Audio") {
            request.addOption("-x")
            request.addOption("--audio-format", "mp3")
            return
        }

        val height = quality.removeSuffix("p").toIntOrNull() ?: 1080
        request.addOption(
            "-f",
            "bestvideo[height<=$height][ext=mp4]+bestaudio[ext=m4a]/best[height<=$height][ext=mp4]/best"
        )
        request.addOption("--merge-output-format", "mp4")
    }

    private fun sendProgress(progress: Float, etaInSeconds: Long, message: String) {
        val normalizedProgress = (progress / 100.0f).coerceIn(0.0f, 1.0f)

        mainHandler.post {
            downloadChannel.invokeMethod(
                "downloadProgress",
                mapOf(
                    "progress" to normalizedProgress.toDouble(),
                    "eta" to etaInSeconds,
                    "message" to message
                )
            )
        }
    }

    private fun publishCompletedFiles(workingDir: File, filesBeforeDownload: Set<String>): List<String> {
        val completedFiles = workingDir.listFiles()
            ?.filter { file ->
                file.isFile &&
                    file.absolutePath !in filesBeforeDownload &&
                    !file.name.endsWith(".part") &&
                    !file.name.endsWith(".ytdl")
            }
            .orEmpty()

        return completedFiles.mapNotNull { file ->
            try {
                publishFile(file)
            } catch (_: Exception) {
                null
            }
        }
    }

    private fun publishFile(sourceFile: File): String {
        val selectedDestination = selectedDestinationUri()
        if (selectedDestination != null) {
            return publishFileToPickedDirectory(sourceFile, selectedDestination)
        }

        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            publishFileWithMediaStore(sourceFile)
        } else {
            publishFileDirectly(sourceFile)
        }
    }

    private fun publishFileToPickedDirectory(sourceFile: File, treeUri: Uri): String {
        val documentId = DocumentsContract.getTreeDocumentId(treeUri)
        val parentUri = DocumentsContract.buildDocumentUriUsingTree(treeUri, documentId)
        val targetUri = DocumentsContract.createDocument(
            contentResolver,
            parentUri,
            mimeTypeFor(sourceFile),
            sourceFile.name
        ) ?: throw IllegalStateException("Impossible de creer le fichier dans le dossier choisi.")

        contentResolver.openOutputStream(targetUri)?.use { output ->
            FileInputStream(sourceFile).use { input -> input.copyTo(output) }
        } ?: throw IllegalStateException("Impossible d'ecrire dans le dossier choisi.")

        return "${destinationLabel()}/${sourceFile.name}"
    }

    private fun publishFileWithMediaStore(sourceFile: File): String {
        val resolver = applicationContext.contentResolver
        val values = ContentValues().apply {
            put(MediaStore.Downloads.DISPLAY_NAME, sourceFile.name)
            put(MediaStore.Downloads.MIME_TYPE, mimeTypeFor(sourceFile))
            put(MediaStore.Downloads.RELATIVE_PATH, "Download/YouTube Downloader")
            put(MediaStore.Downloads.IS_PENDING, 1)
        }

        val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
            ?: throw IllegalStateException("Impossible de creer le fichier public.")

        resolver.openOutputStream(uri)?.use { output ->
            FileInputStream(sourceFile).use { input -> input.copyTo(output) }
        } ?: throw IllegalStateException("Impossible d'ecrire le fichier public.")

        values.clear()
        values.put(MediaStore.Downloads.IS_PENDING, 0)
        resolver.update(uri, values, null, null)

        return "Download/YouTube Downloader/${sourceFile.name}"
    }

    private fun publishFileDirectly(sourceFile: File): String {
        val publicDir = File(
            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
            "YouTube Downloader"
        )
        publicDir.mkdirs()

        val destinationFile = File(publicDir, sourceFile.name)
        FileInputStream(sourceFile).use { input ->
            FileOutputStream(destinationFile).use { output -> input.copyTo(output) }
        }

        return destinationFile.absolutePath
    }

    private fun mimeTypeFor(file: File): String {
        return when (file.extension.lowercase()) {
            "mp3" -> "audio/mpeg"
            "m4a" -> "audio/mp4"
            "webm" -> "video/webm"
            "mkv" -> "video/x-matroska"
            else -> "video/mp4"
        }
    }

    private fun selectedDestinationUri(): Uri? {
        val rawUri = preferences().getString("destination_uri", null) ?: return null
        return Uri.parse(rawUri)
    }

    private fun destinationLabel(): String {
        return preferences().getString("destination_label", null)
            ?: "Telechargements/YouTube Downloader"
    }

    private fun readableName(uri: Uri): String {
        val treeId = DocumentsContract.getTreeDocumentId(uri)
        return treeId.substringAfter(':', treeId).ifBlank { "Dossier selectionne" }
    }

    private fun preferences() = getSharedPreferences("downloads", MODE_PRIVATE)
}
