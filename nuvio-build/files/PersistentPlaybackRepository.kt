package com.nuvio.app.features.player

import com.nuvio.app.features.streams.StreamItem
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

@Serializable
internal data class PersistentPlaybackGlobals(
    val defaultPlaybackSpeed: Float = 1f,
    val rememberPerTitle: Boolean = true,
    val preferEmbeddedSubtitles: Boolean = true,
    val subtitleFallbackChainEnabled: Boolean = true,
    val preferredAudioLanguages: List<String> = emptyList(),
)

@Serializable
internal data class PersistedSourcePin(
    val bingeGroup: String? = null,
    val addonId: String = "",
    val addonName: String? = null,
    val sourceName: String? = null,
    val streamLabel: String? = null,
    val filename: String? = null,
    val releaseSignature: String? = null,
)

@Serializable
internal data class PersistentTrackPreferenceMirror(
    val subtitleType: String? = null,
    val subtitleLanguage: String? = null,
    val subtitleName: String? = null,
    val subtitleTrackId: String? = null,
    val addonSubtitleId: String? = null,
    val addonSubtitleUrl: String? = null,
    val addonSubtitleAddonName: String? = null,
    val audioLanguage: String? = null,
    val audioName: String? = null,
    val audioTrackId: String? = null,
    val subtitleIsForced: Boolean? = null,
) {
    fun toPlayerPreference() = PersistedPlayerTrackPreference(
        subtitleType = subtitleType,
        subtitleLanguage = subtitleLanguage,
        subtitleName = subtitleName,
        subtitleTrackId = subtitleTrackId,
        addonSubtitleId = addonSubtitleId,
        addonSubtitleUrl = addonSubtitleUrl,
        addonSubtitleAddonName = addonSubtitleAddonName,
        audioLanguage = audioLanguage,
        audioName = audioName,
        audioTrackId = audioTrackId,
        subtitleIsForced = subtitleIsForced,
    )

    companion object {
        fun from(value: PersistedPlayerTrackPreference) = PersistentTrackPreferenceMirror(
            subtitleType = value.subtitleType,
            subtitleLanguage = value.subtitleLanguage,
            subtitleName = value.subtitleName,
            subtitleTrackId = value.subtitleTrackId,
            addonSubtitleId = value.addonSubtitleId,
            addonSubtitleUrl = value.addonSubtitleUrl,
            addonSubtitleAddonName = value.addonSubtitleAddonName,
            audioLanguage = value.audioLanguage,
            audioName = value.audioName,
            audioTrackId = value.audioTrackId,
            subtitleIsForced = value.subtitleIsForced,
        )
    }
}

@Serializable
internal data class PersistentTitleSettings(
    val playbackSpeed: Float? = null,
    val seasonPins: Map<String, PersistedSourcePin> = emptyMap(),
    val trackPreference: PersistentTrackPreferenceMirror? = null,
)

@Serializable
internal data class PersistentPlaybackState(
    val version: Int = 1,
    val globals: PersistentPlaybackGlobals = PersistentPlaybackGlobals(),
    val titles: Map<String, PersistentTitleSettings> = emptyMap(),
)

internal object PersistentPlaybackRepository {
    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
        prettyPrint = true
    }
    private val _state = MutableStateFlow(PersistentPlaybackState())
    val state: StateFlow<PersistentPlaybackState> = _state.asStateFlow()
    private var loaded = false

    fun ensureLoaded(): StateFlow<PersistentPlaybackState> {
        if (!loaded) {
            loaded = true
            _state.value = PlayerSettingsStorage.loadPersistentPlaybackStateJson()
                ?.let { raw -> runCatching { json.decodeFromString<PersistentPlaybackState>(raw) }.getOrNull() }
                ?: PersistentPlaybackState()
        }
        return state
    }

    private fun update(transform: (PersistentPlaybackState) -> PersistentPlaybackState) {
        ensureLoaded()
        _state.value = transform(_state.value)
        PlayerSettingsStorage.savePersistentPlaybackStateJson(json.encodeToString(_state.value))
    }

    fun exportBackup(): String {
        ensureLoaded()
        return json.encodeToString(_state.value)
    }

    fun importBackup(raw: String): Boolean {
        val imported = runCatching { json.decodeFromString<PersistentPlaybackState>(raw.trim()) }.getOrNull()
            ?: return false
        if (imported.version != 1) return false
        _state.value = imported
        loaded = true
        PlayerSettingsStorage.savePersistentPlaybackStateJson(json.encodeToString(imported))
        imported.titles.forEach { (contentId, titleSettings) ->
            titleSettings.trackPreference?.let {
                PlayerTrackPreferenceStorage.save(contentId, it.toPlayerPreference())
            }
        }
        return true
    }

    fun setDefaultPlaybackSpeed(speed: Float) = update { current ->
        current.copy(globals = current.globals.copy(defaultPlaybackSpeed = speed.coerceIn(0.25f, 4f)))
    }

    fun setRememberPerTitle(enabled: Boolean) = update { current ->
        current.copy(globals = current.globals.copy(rememberPerTitle = enabled))
    }

    fun setPreferEmbeddedSubtitles(enabled: Boolean) = update { current ->
        current.copy(globals = current.globals.copy(preferEmbeddedSubtitles = enabled))
    }

    fun setSubtitleFallbackChainEnabled(enabled: Boolean) = update { current ->
        current.copy(globals = current.globals.copy(subtitleFallbackChainEnabled = enabled))
    }

    fun setPreferredAudioLanguages(languages: List<String>) = update { current ->
        val normalized = languages.map { it.trim().lowercase() }.filter { it.isNotBlank() }.distinct()
        current.copy(globals = current.globals.copy(preferredAudioLanguages = normalized))
    }

    fun rememberPerTitleEnabled(): Boolean {
        ensureLoaded()
        return _state.value.globals.rememberPerTitle
    }

    fun effectivePlaybackSpeed(contentId: String): Float {
        ensureLoaded()
        val globals = _state.value.globals
        return if (globals.rememberPerTitle) {
            _state.value.titles[contentId]?.playbackSpeed ?: globals.defaultPlaybackSpeed
        } else {
            globals.defaultPlaybackSpeed
        }
    }

    fun persistPlaybackSpeed(contentId: String, speed: Float) {
        ensureLoaded()
        if (!_state.value.globals.rememberPerTitle) {
            setDefaultPlaybackSpeed(speed)
            return
        }
        update { current ->
            val existing = current.titles[contentId] ?: PersistentTitleSettings()
            current.copy(titles = current.titles + (contentId to existing.copy(playbackSpeed = speed)))
        }
    }

    fun setTrackPreference(contentId: String, preference: PersistedPlayerTrackPreference) {
        if (!rememberPerTitleEnabled()) return
        update { current ->
            val existing = current.titles[contentId] ?: PersistentTitleSettings()
            current.copy(
                titles = current.titles + (
                    contentId to existing.copy(
                        trackPreference = PersistentTrackPreferenceMirror.from(preference),
                    )
                )
            )
        }
    }

    fun titleSettings(contentId: String): PersistentTitleSettings? {
        ensureLoaded()
        return _state.value.titles[contentId]
    }

    fun seasonPin(contentId: String, season: Int?): PersistedSourcePin? {
        if (season == null) return null
        return titleSettings(contentId)?.seasonPins?.get(season.toString())
    }

    fun toggleSeasonPin(contentId: String, season: Int, stream: StreamItem): Boolean {
        val newPin = stream.toPersistentSourcePin()
        var pinned = false
        update { current ->
            val existing = current.titles[contentId] ?: PersistentTitleSettings()
            val key = season.toString()
            val currentPin = existing.seasonPins[key]
            val nextPins = if (currentPin != null && stream.matchesPersistentPin(currentPin)) {
                existing.seasonPins - key
            } else {
                pinned = true
                existing.seasonPins + (key to newPin)
            }
            current.copy(titles = current.titles + (contentId to existing.copy(seasonPins = nextPins)))
        }
        return pinned
    }

    fun resetTitle(contentId: String) {
        update { current -> current.copy(titles = current.titles - contentId) }
        PlayerTrackPreferenceStorage.save(contentId, PersistedPlayerTrackPreference())
    }
}

internal fun StreamItem.toPersistentSourcePin(): PersistedSourcePin = PersistedSourcePin(
    bingeGroup = behaviorHints.bingeGroup?.trim()?.takeIf { it.isNotBlank() },
    addonId = addonId,
    addonName = addonName,
    sourceName = sourceName,
    streamLabel = streamLabel,
    filename = behaviorHints.filename,
    releaseSignature = persistentReleaseSignature(),
)

internal fun StreamItem.matchesPersistentPin(pin: PersistedSourcePin): Boolean {
    val streamBingeGroup = behaviorHints.bingeGroup?.trim()?.takeIf { it.isNotBlank() }
    val pinBingeGroup = pin.bingeGroup?.trim()?.takeIf { it.isNotBlank() }
    if (streamBingeGroup != null && pinBingeGroup != null) {
        return streamBingeGroup == pinBingeGroup && (pin.addonId.isBlank() || pin.addonId == addonId)
    }
    if (pin.addonId.isNotBlank() && pin.addonId != addonId) return false
    val expected = pin.releaseSignature?.takeIf { it.isNotBlank() } ?: return false
    return persistentReleaseSignature() == expected
}

internal fun StreamItem.persistentReleaseSignature(): String {
    val raw = listOfNotNull(
        streamLabel,
        behaviorHints.filename,
        sourceName,
        addonName,
    ).joinToString(" ")
    return normalizePersistentReleaseSignature(raw)
}

private fun normalizePersistentReleaseSignature(raw: String): String = raw
    .lowercase()
    .replace(Regex("""\bs\d{1,2}e\d{1,3}\b"""), " ")
    .replace(Regex("""\b\d{1,2}x\d{1,3}\b"""), " ")
    .replace(Regex("""\bepisode[\s._-]*\d{1,4}\b"""), " ")
    .replace(Regex("""\bep[\s._-]*\d{1,4}\b"""), " ")
    .replace(Regex("""\b\d{1,2}[\s._-]*of[\s._-]*\d{1,3}\b"""), " ")
    .replace(Regex("""[^a-z0-9]+"""), " ")
    .trim()
    .replace(Regex("""\s+"""), " ")
