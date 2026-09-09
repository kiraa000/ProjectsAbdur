package com.nuvio.app.features.player

internal fun PlayerScreenRuntime.applyPersistentSubtitleFallbackIfAvailable(
    preferredSubtitleTargets: List<String>,
    selectedAudioTrack: AudioTrack?,
): Boolean {
    PersistentPlaybackRepository.ensureLoaded()
    val globals = PersistentPlaybackRepository.state.value.globals
    if (!globals.subtitleFallbackChainEnabled) return false
    if (preferredSubtitleTargets.isEmpty()) return false
    if (!hasScannedTextTracksOnce || playbackSnapshot.isLoading) return true

    val normalInternal = findBestInternalSubtitleTrackIndex(
        tracks = subtitleTracks,
        targets = preferredSubtitleTargets,
        normalOnly = true,
        selectedAudioTrack = selectedAudioTrack,
    ).takeIf { it >= 0 }

    val normalAddon = preferredSubtitleTargets.firstNotNullOfOrNull { target ->
        addonSubtitles.firstOrNull { subtitle ->
            !addonSubtitleIsForced(subtitle) && addonSubtitleMatchesLanguage(subtitle, target)
        }
    }

    val forcedInternal = preferredSubtitleTargets.firstNotNullOfOrNull { target ->
        findBestForcedSubtitleTrackIndex(
            tracks = subtitleTracks,
            target = target,
            selectedAudioTrack = selectedAudioTrack,
        ).takeIf { it >= 0 }
    }

    val forcedAddon = preferredSubtitleTargets.firstNotNullOfOrNull { target ->
        addonSubtitles.firstOrNull { subtitle ->
            addonSubtitleIsForced(subtitle) &&
                addonSubtitleMatchesLanguage(subtitle, target) &&
                (selectedAudioTrack == null || addonSubtitleMatchesSelectedAudioLanguage(subtitle, selectedAudioTrack))
        }
    }

    if (!globals.preferEmbeddedSubtitles && isLoadingAddonSubtitles && normalAddon == null) {
        return true
    }

    fun selectInternal(index: Int) {
        preferredSubtitleSelectionApplied = true
        if (selectedSubtitleIndex != index || selectedAddonSubtitleId != null) {
            if (useCustomSubtitles) {
                playerController?.clearExternalSubtitleAndSelect(index)
            } else {
                playerController?.selectSubtitleTrack(index)
            }
            selectedSubtitleIndex = index
            selectedAddonSubtitleId = null
            useCustomSubtitles = false
        }
    }

    fun selectAddon(subtitle: AddonSubtitle) {
        preferredSubtitleSelectionApplied = true
        selectedAddonSubtitleId = subtitle.selectionKey
        selectedSubtitleIndex = -1
        useCustomSubtitles = true
        playerController?.setSubtitleUri(subtitle.url)
    }

    if (globals.preferEmbeddedSubtitles) {
        if (normalInternal != null) { selectInternal(normalInternal); return true }
        if (normalAddon != null) { selectAddon(normalAddon); return true }
        if (forcedInternal != null) { selectInternal(forcedInternal); return true }
        if (forcedAddon != null) { selectAddon(forcedAddon); return true }
    } else {
        if (normalAddon != null) { selectAddon(normalAddon); return true }
        if (normalInternal != null) { selectInternal(normalInternal); return true }
        if (forcedAddon != null) { selectAddon(forcedAddon); return true }
        if (forcedInternal != null) { selectInternal(forcedInternal); return true }
    }

    if (isLoadingAddonSubtitles) return true
    preferredSubtitleSelectionApplied = true
    playerController?.selectSubtitleTrack(-1)
    selectedSubtitleIndex = -1
    selectedAddonSubtitleId = null
    useCustomSubtitles = false
    return true
}
