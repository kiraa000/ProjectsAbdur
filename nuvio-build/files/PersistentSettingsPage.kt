package com.nuvio.app.features.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyListScope
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.nuvio.app.core.ui.nuvio
import com.nuvio.app.features.player.PersistentPlaybackRepository

internal fun LazyListScope.persistentSettingsContent(
    isTablet: Boolean,
) {
    item {
        val tokens = MaterialTheme.nuvio
        SettingsSection(
            title = "About",
            isTablet = isTablet,
        ) {
            SettingsGroup(isTablet = isTablet) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = if (isTablet) 20.dp else 16.dp, vertical = if (isTablet) 16.dp else 14.dp),
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                ) {
                    Text(
                        text = "Persistent playback settings",
                        style = MaterialTheme.typography.bodyLarge,
                        color = tokens.colors.textPrimary,
                    )
                    Text(
                        text = "Per title playback rules are stored locally and intentionally stay separate from Nuvio Sync.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = tokens.colors.textMuted,
                    )
                }
            }
        }
    }

    item {
        val stateFlow = remember { PersistentPlaybackRepository.ensureLoaded() }
        val state by stateFlow.collectAsStateWithLifecycle()
        val globals = state.globals

        SettingsSection(
            title = "Playback behavior",
            isTablet = isTablet,
        ) {
            SettingsGroup(isTablet = isTablet) {
                SettingsSwitchRow(
                    title = "Remember per title",
                    description = "Remember playback speed plus explicit audio and subtitle choices for each title.",
                    checked = globals.rememberPerTitle,
                    isTablet = isTablet,
                    onCheckedChange = PersistentPlaybackRepository::setRememberPerTitle,
                )
                SettingsGroupDivider(isTablet = isTablet)
                SettingsSwitchRow(
                    title = "Prefer embedded subtitles",
                    description = "Try embedded subtitles before external subtitles when applying the fallback rules.",
                    checked = globals.preferEmbeddedSubtitles,
                    isTablet = isTablet,
                    onCheckedChange = PersistentPlaybackRepository::setPreferEmbeddedSubtitles,
                )
                SettingsGroupDivider(isTablet = isTablet)
                SettingsSwitchRow(
                    title = "Subtitle fallback chain",
                    description = "Preferred normal subtitle, alternate source, forced subtitle, then none.",
                    checked = globals.subtitleFallbackChainEnabled,
                    isTablet = isTablet,
                    onCheckedChange = PersistentPlaybackRepository::setSubtitleFallbackChainEnabled,
                )
            }
        }
    }

    item {
        val tokens = MaterialTheme.nuvio
        val stateFlow = remember { PersistentPlaybackRepository.ensureLoaded() }
        val state by stateFlow.collectAsStateWithLifecycle()
        val globals = state.globals

        SettingsSection(
            title = "Default playback speed",
            isTablet = isTablet,
        ) {
            SettingsGroup(isTablet = isTablet) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = if (isTablet) 20.dp else 16.dp, vertical = if (isTablet) 16.dp else 14.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Text(
                        text = "Used whenever a title does not have its own saved speed.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = tokens.colors.textMuted,
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        listOf(1f, 1.25f, 1.5f, 2f).forEach { speed ->
                            val selected = kotlin.math.abs(globals.defaultPlaybackSpeed - speed) < 0.01f
                            Button(
                                onClick = { PersistentPlaybackRepository.setDefaultPlaybackSpeed(speed) },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = if (selected) {
                                        tokens.colors.accent
                                    } else {
                                        tokens.colors.surfaceCard
                                    },
                                    contentColor = if (selected) {
                                        tokens.colors.onAccent
                                    } else {
                                        tokens.colors.textPrimary
                                    },
                                ),
                            ) {
                                Text("${speed}x")
                            }
                        }
                    }
                }
            }
        }
    }

    item {
        val tokens = MaterialTheme.nuvio
        val stateFlow = remember { PersistentPlaybackRepository.ensureLoaded() }
        val state by stateFlow.collectAsStateWithLifecycle()
        val globals = state.globals
        var audioLanguages by remember(globals.preferredAudioLanguages) {
            mutableStateOf(globals.preferredAudioLanguages.joinToString(", "))
        }

        SettingsSection(
            title = "Audio language priority",
            isTablet = isTablet,
        ) {
            SettingsGroup(isTablet = isTablet) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = if (isTablet) 20.dp else 16.dp, vertical = if (isTablet) 16.dp else 14.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Text(
                        text = "Comma separated language codes. Example: en, ja, ko",
                        style = MaterialTheme.typography.bodyMedium,
                        color = tokens.colors.textMuted,
                    )
                    OutlinedTextField(
                        value = audioLanguages,
                        onValueChange = { audioLanguages = it },
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("Priority") },
                        singleLine = true,
                    )
                    Button(
                        onClick = {
                            PersistentPlaybackRepository.setPreferredAudioLanguages(audioLanguages.split(","))
                        },
                    ) {
                        Text("Save priority")
                    }
                }
            }
        }
    }

    item {
        val tokens = MaterialTheme.nuvio
        remember { PersistentPlaybackRepository.ensureLoaded() }
        var backupText by remember { mutableStateOf(PersistentPlaybackRepository.exportBackup()) }
        var importStatus by remember { mutableStateOf<String?>(null) }

        SettingsSection(
            title = "Backup and restore",
            isTablet = isTablet,
        ) {
            SettingsGroup(isTablet = isTablet) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = if (isTablet) 20.dp else 16.dp, vertical = if (isTablet) 16.dp else 14.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Text(
                        text = "Includes playback defaults, per title speed, season pins, and remembered track choices. Account tokens are never included.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = tokens.colors.textMuted,
                    )
                    OutlinedTextField(
                        value = backupText,
                        onValueChange = {
                            backupText = it
                            importStatus = null
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 180.dp),
                        label = { Text("Persistent settings JSON") },
                        minLines = 7,
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Button(
                            onClick = {
                                backupText = PersistentPlaybackRepository.exportBackup()
                                importStatus = "Backup refreshed"
                            },
                        ) {
                            Text("Export")
                        }
                        Button(
                            onClick = {
                                importStatus = if (PersistentPlaybackRepository.importBackup(backupText)) {
                                    "Imported successfully"
                                } else {
                                    "Invalid backup JSON"
                                }
                            },
                        ) {
                            Text("Import")
                        }
                    }
                    importStatus?.let { status ->
                        Text(
                            text = status,
                            style = MaterialTheme.typography.bodySmall,
                            color = tokens.colors.textMuted,
                        )
                    }
                }
            }
        }
    }
}