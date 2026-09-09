#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
assets = Path(__file__).resolve().parent / "files"

def path(rel):
    return root / rel

def read(rel):
    return path(rel).read_text(encoding="utf-8")

def write(rel, text):
    target = path(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")

def replace_once(rel, old, new):
    text = read(rel)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Patch anchor count for {rel} was {count}, expected 1: {old[:120]!r}")
    write(rel, text.replace(old, new, 1))

copies = {
    "PersistentPlaybackRepository.kt": "composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PersistentPlaybackRepository.kt",
    "PersistentSubtitleFallback.kt": "composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PersistentSubtitleFallback.kt",
    "PersistentSettingsDialog.kt": "composeApp/src/commonMain/kotlin/com/nuvio/app/features/settings/PersistentSettingsDialog.kt",
}
for source_name, destination in copies.items():
    write(destination, (assets / source_name).read_text(encoding="utf-8"))

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerSettingsStorage.kt', '    fun exportToSyncPayload(): JsonObject\n', '    fun loadPersistentPlaybackStateJson(): String?\n    fun savePersistentPlaybackStateJson(value: String)\n    fun exportToSyncPayload(): JsonObject\n')

replace_once('composeApp/src/androidMain/kotlin/com/nuvio/app/features/player/PlayerSettingsStorage.android.kt', '    private const val iosGammaKey = "ios_gamma"\n', '    private const val iosGammaKey = "ios_gamma"\n    private const val persistentPlaybackStateKey = "abdur_persistent_playback_state_v1"\n')

replace_once('composeApp/src/androidMain/kotlin/com/nuvio/app/features/player/PlayerSettingsStorage.android.kt', '    actual fun exportToSyncPayload(): JsonObject', '    actual fun loadPersistentPlaybackStateJson(): String? =\n        preferences?.getString(ProfileScopedKey.of(persistentPlaybackStateKey), null)\n\n    actual fun savePersistentPlaybackStateJson(value: String) {\n        preferences\n            ?.edit()\n            ?.putString(ProfileScopedKey.of(persistentPlaybackStateKey), value)\n            ?.apply()\n    }\n\n    actual fun exportToSyncPayload(): JsonObject')

replace_once('composeApp/src/iosMain/kotlin/com/nuvio/app/features/player/PlayerSettingsStorage.ios.kt', '    private const val iosGammaKey = "ios_gamma"\n', '    private const val iosGammaKey = "ios_gamma"\n    private const val persistentPlaybackStateKey = "abdur_persistent_playback_state_v1"\n')

replace_once('composeApp/src/iosMain/kotlin/com/nuvio/app/features/player/PlayerSettingsStorage.ios.kt', '    actual fun exportToSyncPayload(): JsonObject', '    actual fun loadPersistentPlaybackStateJson(): String? =\n        NSUserDefaults.standardUserDefaults.stringForKey(ProfileScopedKey.of(persistentPlaybackStateKey))\n\n    actual fun savePersistentPlaybackStateJson(value: String) {\n        NSUserDefaults.standardUserDefaults.setObject(value, forKey = ProfileScopedKey.of(persistentPlaybackStateKey))\n    }\n\n    actual fun exportToSyncPayload(): JsonObject')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerScreenRuntimeTrackActions.kt', 'internal fun PlayerScreenRuntime.updateTrackPreference(\n    update: (PersistedPlayerTrackPreference) -> PersistedPlayerTrackPreference,\n) {\n    if (parentMetaId.isBlank()) return\n    val current = PlayerTrackPreferenceStorage.load(parentMetaId) ?: PersistedPlayerTrackPreference()\n    PlayerTrackPreferenceStorage.save(parentMetaId, update(current))\n}\n', 'internal fun PlayerScreenRuntime.updateTrackPreference(\n    update: (PersistedPlayerTrackPreference) -> PersistedPlayerTrackPreference,\n) {\n    if (parentMetaId.isBlank() || !PersistentPlaybackRepository.rememberPerTitleEnabled()) return\n    val current = PlayerTrackPreferenceStorage.load(parentMetaId) ?: PersistedPlayerTrackPreference()\n    val updated = update(current)\n    PlayerTrackPreferenceStorage.save(parentMetaId, updated)\n    PersistentPlaybackRepository.setTrackPreference(parentMetaId, updated)\n}\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerScreenRuntimeTrackActions.kt', 'internal fun PlayerScreenRuntime.restorePersistedTrackPreferenceIfNeeded() {\n    if (trackPreferenceRestoreApplied) return\n    val preference = PlayerTrackPreferenceStorage.load(parentMetaId)\n', 'internal fun PlayerScreenRuntime.restorePersistedTrackPreferenceIfNeeded() {\n    if (trackPreferenceRestoreApplied) return\n    if (!PersistentPlaybackRepository.rememberPerTitleEnabled()) {\n        trackPreferenceRestoreApplied = true\n        return\n    }\n    val preference = PlayerTrackPreferenceStorage.load(parentMetaId)\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerScreenRuntimeAudioPreferences.kt', 'internal val PlayerScreenRuntime.preferredAudioLanguageTargets: List<String>\n    get() = resolvePreferredAudioLanguageTargets(\n        preferredAudioLanguage = playerSettingsUiState.preferredAudioLanguage,\n        secondaryPreferredAudioLanguage = playerSettingsUiState.secondaryPreferredAudioLanguage,\n        deviceLanguages = DeviceLanguagePreferences.preferredLanguageCodes(),\n        contentOriginalLanguage = contentLanguage,\n    )\n', 'internal val PlayerScreenRuntime.preferredAudioLanguageTargets: List<String>\n    get() {\n        PersistentPlaybackRepository.ensureLoaded()\n        val custom = PersistentPlaybackRepository.state.value.globals.preferredAudioLanguages\n        return if (custom.isNotEmpty()) {\n            custom\n        } else {\n            resolvePreferredAudioLanguageTargets(\n                preferredAudioLanguage = playerSettingsUiState.preferredAudioLanguage,\n                secondaryPreferredAudioLanguage = playerSettingsUiState.secondaryPreferredAudioLanguage,\n                deviceLanguages = DeviceLanguagePreferences.preferredLanguageCodes(),\n                contentOriginalLanguage = contentLanguage,\n            )\n        }\n    }\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerScreenRuntimeTrackActions.kt', '    val selectedAudioTrack = audioTracks.firstOrNull { track -> track.index == selectedAudioIndex }\n        ?: audioTracks.firstOrNull { it.isSelected }\n    val selectionPlan = resolveSubtitleAutoSelectionPlan(\n', '    val selectedAudioTrack = audioTracks.firstOrNull { track -> track.index == selectedAudioIndex }\n        ?: audioTracks.firstOrNull { it.isSelected }\n    if (applyPersistentSubtitleFallbackIfAvailable(preferredSubtitleTargets, selectedAudioTrack)) {\n        return\n    }\n    val selectionPlan = resolveSubtitleAutoSelectionPlan(\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerScreenRuntimeGestureActions.kt', '    playerController?.setPlaybackSpeed(next)\n    showGestureMessage(formatPlaybackSpeedLabel(next))\n', '    playerController?.setPlaybackSpeed(next)\n    PersistentPlaybackRepository.persistPlaybackSpeed(parentMetaId, next)\n    showGestureMessage(formatPlaybackSpeedLabel(next))\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerScreenRuntimeUi.kt', '                onControllerReady = { controller ->\n                    playerController = controller\n                    playerControllerSourceUrl = playerSurfaceSourceUrl\n                },\n', '                onControllerReady = { controller ->\n                    playerController = controller\n                    playerControllerSourceUrl = playerSurfaceSourceUrl\n                    controller.setPlaybackSpeed(PersistentPlaybackRepository.effectivePlaybackSpeed(parentMetaId))\n                },\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/StreamCard.kt', '    isCurrent: Boolean = false,\n    currentLabel: String? = null,\n) {\n', '    isCurrent: Boolean = false,\n    currentLabel: String? = null,\n    statusLabel: String? = null,\n) {\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/StreamCard.kt', '                if (isCurrent && !currentLabel.isNullOrBlank()) {\n                    Spacer(modifier = Modifier.width(8.dp))\n                    CurrentStreamBadge(label = currentLabel)\n                }\n', '                if (isCurrent && !currentLabel.isNullOrBlank()) {\n                    Spacer(modifier = Modifier.width(8.dp))\n                    CurrentStreamBadge(label = currentLabel)\n                }\n                if (!statusLabel.isNullOrBlank()) {\n                    Spacer(modifier = Modifier.width(8.dp))\n                    CurrentStreamBadge(label = statusLabel)\n                }\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerStreamList.kt', '    currentStreamName: String? = null,\n    currentLabel: String? = null,\n) {\n', '    currentStreamName: String? = null,\n    currentLabel: String? = null,\n    statusLabelForStream: ((StreamItem) -> String?)? = null,\n    onStreamLongClick: ((StreamItem) -> Unit)? = null,\n) {\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerStreamList.kt', '                        currentLabel = currentLabel,\n                        onClick = { onStreamSelected(stream) },\n                    )\n', '                        currentLabel = currentLabel,\n                        statusLabel = statusLabelForStream?.invoke(stream),\n                        onClick = { onStreamSelected(stream) },\n                        onLongClick = onStreamLongClick?.let { callback -> { callback(stream) } },\n                    )\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerSourcesPanel.kt', '    contentTitle: String,\n    currentSeason: Int?,\n', '    contentTitle: String,\n    parentMetaId: String,\n    currentSeason: Int?,\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerSourcesPanel.kt', 'import com.nuvio.app.core.ui.nuvio\n', 'import com.nuvio.app.core.ui.NuvioToastController\nimport com.nuvio.app.core.ui.nuvio\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerSourcesPanel.kt', '    val tokens = MaterialTheme.nuvio\n    val addonGroups = streamsUiState.groups\n', '    val tokens = MaterialTheme.nuvio\n    val persistentStateFlow = remember { PersistentPlaybackRepository.ensureLoaded() }\n    val persistentState by persistentStateFlow.collectAsStateWithLifecycle()\n    val titleSettings = persistentState.titles[parentMetaId]\n    val seasonPin = currentSeason?.let { titleSettings?.seasonPins?.get(it.toString()) }\n    val addonGroups = streamsUiState.groups\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerSourcesPanel.kt', '                PlayerDialogButton(\n                    label = stringResource(Res.string.action_close),\n                    onClick = onDismiss,\n                )\n', '                if (titleSettings != null && (\n                        titleSettings.playbackSpeed != null ||\n                            titleSettings.seasonPins.isNotEmpty() ||\n                            titleSettings.trackPreference != null\n                    )\n                ) {\n                    PlayerDialogButton(\n                        label = "Reset title",\n                        onClick = {\n                            PersistentPlaybackRepository.resetTitle(parentMetaId)\n                            NuvioToastController.show("Per-title settings reset")\n                        },\n                    )\n                }\n                PlayerDialogButton(\n                    label = stringResource(Res.string.action_close),\n                    onClick = onDismiss,\n                )\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerSourcesPanel.kt', '            Spacer(Modifier.height(16.dp))\n\n            if (addonGroups.isNotEmpty()) {\n', '            if (titleSettings != null && (\n                    titleSettings.playbackSpeed != null ||\n                        titleSettings.seasonPins.isNotEmpty() ||\n                        titleSettings.trackPreference != null\n                )\n            ) {\n                Spacer(Modifier.height(6.dp))\n                val customSummary = buildString {\n                    append("Custom settings")\n                    titleSettings.playbackSpeed?.let { append(" • ${it}x") }\n                    if (seasonPin != null && currentSeason != null) append(" • Pinned for Season $currentSeason")\n                }\n                Text(\n                    text = customSummary,\n                    color = MaterialTheme.colorScheme.primary,\n                    style = MaterialTheme.typography.bodySmall,\n                )\n            }\n\n            Spacer(Modifier.height(16.dp))\n\n            if (addonGroups.isNotEmpty()) {\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerSourcesPanel.kt', '                currentStreamName = currentStreamName,\n                currentLabel = stringResource(Res.string.compose_player_playing),\n            )\n', '                currentStreamName = currentStreamName,\n                currentLabel = stringResource(Res.string.compose_player_playing),\n                statusLabelForStream = { stream ->\n                    if (seasonPin != null && currentSeason != null && stream.matchesPersistentPin(seasonPin)) {\n                        "Pinned S$currentSeason"\n                    } else {\n                        null\n                    }\n                },\n                onStreamLongClick = { stream ->\n                    val season = currentSeason\n                    if (season != null) {\n                        val pinned = PersistentPlaybackRepository.toggleSeasonPin(parentMetaId, season, stream)\n                        NuvioToastController.show(\n                            if (pinned) "Pinned for Season $season" else "Source unpinned for Season $season",\n                        )\n                    }\n                },\n            )\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerScreenModalHosts.kt', '        contentTitle = contentTitle,\n        currentSeason = activeSeasonNumber,\n', '        contentTitle = contentTitle,\n        parentMetaId = parentMetaId,\n        currentSeason = activeSeasonNumber,\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerNextEpisodeAutoPlay.kt', 'import com.nuvio.app.features.addons.enabledAddons\n', 'import com.nuvio.app.features.addons.enabledAddons\nimport com.nuvio.app.core.ui.NuvioToastController\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerNextEpisodeAutoPlay.kt', '    val type = contentType ?: parentMetaType\n', '    val type = contentType ?: parentMetaType\n    val explicitPin = PersistentPlaybackRepository.seasonPin(parentMetaId, nextVideo.season)\n    var pinFallbackNotified = false\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerNextEpisodeAutoPlay.kt', '        fun trySelectStream(streams: List<StreamItem>): StreamItem? =\n            StreamAutoPlaySelector.selectAutoPlayStream(\n', '        fun trySelectStream(streams: List<StreamItem>): StreamItem? {\n            explicitPin?.let { pin ->\n                streams.firstOrNull { it.matchesPersistentPin(pin) }?.let { return it }\n            }\n            return StreamAutoPlaySelector.selectAutoPlayStream(\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerNextEpisodeAutoPlay.kt', '                activeResolverProviderId = debridSettings.activeResolverProviderId,\n            )\n\n        fun tryBingeGroupOnly(streams: List<StreamItem>): StreamItem? {\n', '                activeResolverProviderId = debridSettings.activeResolverProviderId,\n            )\n        }\n\n        fun tryBingeGroupOnly(streams: List<StreamItem>): StreamItem? {\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerNextEpisodeAutoPlay.kt', '                if (!autoSelectTriggered && !state.isAnyLoading) {\n                    if (allStreams.isNotEmpty()) {\n', '                if (!autoSelectTriggered && !state.isAnyLoading) {\n                    if (explicitPin != null && !pinFallbackNotified &&\n                        allStreams.none { it.matchesPersistentPin(explicitPin) }\n                    ) {\n                        pinFallbackNotified = true\n                        NuvioToastController.show(\n                            "Pinned source unavailable for S${nextVideo.season ?: 0}E${nextVideo.episode ?: 0}. Using normal source selection.",\n                        )\n                    }\n                    if (allStreams.isNotEmpty()) {\n')

replace_once('composeApp/src/commonMain/kotlin/com/nuvio/app/features/settings/AdvancedSettingsPage.kt', '    item {\n        SettingsSection(\n            title = stringResource(Res.string.settings_advanced_section_cache),\n', '    item {\n        var showPersistentSettings by rememberSaveable { mutableStateOf(false) }\n        SettingsSection(\n            title = "Playback persistence",\n            isTablet = isTablet,\n        ) {\n            SettingsGroup(isTablet = isTablet) {\n                SettingsNavigationRow(\n                    title = "Persistent Settings",\n                    description = "Per-title speed, audio/subtitle memory, season source pins, fallback rules, and backup.",\n                    isTablet = isTablet,\n                    onClick = { showPersistentSettings = true },\n                )\n            }\n        }\n        if (showPersistentSettings) {\n            PersistentSettingsDialog(onDismiss = { showPersistentSettings = false })\n        }\n    }\n    item {\n        SettingsSection(\n            title = stringResource(Res.string.settings_advanced_section_cache),\n')

replace_once('androidApp/build.gradle.kts', '        applicationId = "com.nuvio.media"\n', '        applicationId = "com.nuvio.media.abdur"\n')

print("Applied Nuvio Enhanced custom persistence patch.")
