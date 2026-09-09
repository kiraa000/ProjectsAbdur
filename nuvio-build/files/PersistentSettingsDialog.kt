package com.nuvio.app.features.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.BasicAlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.nuvio.app.core.ui.nuvio
import com.nuvio.app.features.player.PersistentPlaybackRepository

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun PersistentSettingsDialog(onDismiss: () -> Unit) {
    val tokens = MaterialTheme.nuvio
    val stateFlow = remember { PersistentPlaybackRepository.ensureLoaded() }
    val state by stateFlow.collectAsStateWithLifecycle()
    val globals = state.globals
    var audioLanguages by remember(globals.preferredAudioLanguages) {
        mutableStateOf(globals.preferredAudioLanguages.joinToString(", "))
    }
    var backupText by remember { mutableStateOf(PersistentPlaybackRepository.exportBackup()) }
    var importStatus by remember { mutableStateOf<String?>(null) }

    BasicAlertDialog(onDismissRequest = onDismiss) {
        Surface(
            modifier = Modifier.fillMaxWidth(),
            color = tokens.colors.surfaceDialog,
            shape = tokens.shapes.dialog,
        ) {
            Column(
                modifier = Modifier
                    .padding(tokens.spacing.dialogPadding)
                    .heightIn(max = 700.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text("Persistent Settings", style = MaterialTheme.typography.titleLarge)
                Text(
                    "Local playback rules. These are intentionally excluded from Nuvio Sync.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = tokens.colors.textMuted,
                )

                Text("Default playback speed", style = MaterialTheme.typography.titleSmall)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf(1f, 1.25f, 1.5f, 2f).forEach { speed ->
                        Button(
                            onClick = { PersistentPlaybackRepository.setDefaultPlaybackSpeed(speed) },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (kotlin.math.abs(globals.defaultPlaybackSpeed - speed) < 0.01f) {
                                    MaterialTheme.colorScheme.primary
                                } else {
                                    tokens.colors.surfaceCard
                                },
                            ),
                        ) { Text("${speed}x") }
                    }
                }

                PersistentSwitchLine(
                    title = "Remember per title",
                    description = "Remember speed plus explicit audio and subtitle choices for each title.",
                    checked = globals.rememberPerTitle,
                    onCheckedChange = PersistentPlaybackRepository::setRememberPerTitle,
                )
                PersistentSwitchLine(
                    title = "Prefer embedded subtitles",
                    description = "Fallback starts with embedded subtitles, then external, then forced.",
                    checked = globals.preferEmbeddedSubtitles,
                    onCheckedChange = PersistentPlaybackRepository::setPreferEmbeddedSubtitles,
                )
                PersistentSwitchLine(
                    title = "Subtitle fallback chain",
                    description = "Preferred normal subtitle, alternate source, forced subtitle, then none.",
                    checked = globals.subtitleFallbackChainEnabled,
                    onCheckedChange = PersistentPlaybackRepository::setSubtitleFallbackChainEnabled,
                )

                OutlinedTextField(
                    value = audioLanguages,
                    onValueChange = { audioLanguages = it },
                    label = { Text("Audio language priority") },
                    supportingText = { Text("Comma separated language codes, for example: en, ja, ko") },
                    modifier = Modifier.fillMaxWidth(),
                )
                Button(
                    onClick = { PersistentPlaybackRepository.setPreferredAudioLanguages(audioLanguages.split(",")) },
                ) { Text("Save audio priority") }

                Text("Backup and restore", style = MaterialTheme.typography.titleSmall)
                Text(
                    "Includes playback defaults, per title speed, season pins, and remembered track choices. Account tokens are not included.",
                    style = MaterialTheme.typography.bodySmall,
                    color = tokens.colors.textMuted,
                )
                OutlinedTextField(
                    value = backupText,
                    onValueChange = { backupText = it; importStatus = null },
                    label = { Text("Persistent settings JSON") },
                    modifier = Modifier.fillMaxWidth().heightIn(min = 180.dp),
                    minLines = 7,
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = {
                            backupText = PersistentPlaybackRepository.exportBackup()
                            importStatus = "Backup refreshed"
                        },
                    ) { Text("Export") }
                    Button(
                        onClick = {
                            importStatus = if (PersistentPlaybackRepository.importBackup(backupText)) {
                                "Imported successfully"
                            } else {
                                "Invalid backup JSON"
                            }
                        },
                    ) { Text("Import") }
                }
                importStatus?.let { Text(it, style = MaterialTheme.typography.bodySmall) }

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                    Button(onClick = onDismiss) { Text("Close") }
                }
            }
        }
    }
}

@Composable
private fun PersistentSwitchLine(
    title: String,
    description: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.bodyLarge)
            Text(
                description,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Spacer(Modifier.width(12.dp))
        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}
