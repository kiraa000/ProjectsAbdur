#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
assets = Path(__file__).resolve().parent / "files"


def path(rel: str) -> Path:
    return root / rel


def read(rel: str) -> str:
    return path(rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    target = path(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def replace_once(rel: str, old: str, new: str) -> None:
    text = read(rel)
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"Native-page patch anchor count for {rel} was {count}, expected 1: {old[:160]!r}"
        )
    write(rel, text.replace(old, new, 1))


# The first custom patch installs the persistence repository and a temporary dialog.
# Replace only the presentation/navigation layer here so player behavior remains untouched.
page_destination = (
    "composeApp/src/commonMain/kotlin/com/nuvio/app/features/settings/PersistentSettingsPage.kt"
)
write(page_destination, (assets / "PersistentSettingsPage.kt").read_text(encoding="utf-8"))

legacy_dialog = path(
    "composeApp/src/commonMain/kotlin/com/nuvio/app/features/settings/PersistentSettingsDialog.kt"
)
if legacy_dialog.exists():
    legacy_dialog.unlink()

advanced = "composeApp/src/commonMain/kotlin/com/nuvio/app/features/settings/AdvancedSettingsPage.kt"
replace_once(
    advanced,
    """internal fun LazyListScope.advancedSettingsContent(
    isTablet: Boolean,
    rememberLastProfileEnabled: Boolean,
    onDebugLogsClick: () -> Unit,
) {
""",
    """internal fun LazyListScope.advancedSettingsContent(
    isTablet: Boolean,
    rememberLastProfileEnabled: Boolean,
    onPersistentSettingsClick: () -> Unit,
    onDebugLogsClick: () -> Unit,
) {
""",
)

replace_once(
    advanced,
    """    item {
        var showPersistentSettings by rememberSaveable { mutableStateOf(false) }
        SettingsSection(
            title = "Playback persistence",
            isTablet = isTablet,
        ) {
            SettingsGroup(isTablet = isTablet) {
                SettingsNavigationRow(
                    title = "Persistent Settings",
                    description = "Per-title speed, audio/subtitle memory, season source pins, fallback rules, and backup.",
                    isTablet = isTablet,
                    onClick = { showPersistentSettings = true },
                )
            }
        }
        if (showPersistentSettings) {
            PersistentSettingsDialog(onDismiss = { showPersistentSettings = false })
        }
    }
""",
    """    item {
        SettingsSection(
            title = "Playback persistence",
            isTablet = isTablet,
        ) {
            SettingsGroup(isTablet = isTablet) {
                SettingsNavigationRow(
                    title = "Persistent Settings",
                    description = "Per-title speed, audio and subtitle memory, season source pins, fallback rules, and backup.",
                    isTablet = isTablet,
                    onClick = onPersistentSettingsClick,
                )
            }
        }
    }
""",
)

models = "composeApp/src/commonMain/kotlin/com/nuvio/app/features/settings/SettingsModels.kt"
replace_once(
    models,
    "import nuvio.composeapp.generated.resources.compose_settings_page_debug_logs\n",
    "import nuvio.composeapp.generated.resources.compose_settings_page_debug_logs\n"
    "import nuvio.composeapp.generated.resources.compose_settings_page_persistent_settings\n",
)
replace_once(
    models,
    """    DebugLogs(
        titleRes = Res.string.compose_settings_page_debug_logs,
        category = SettingsCategory.Advanced,
        parentPage = Advanced,
    ),
""",
    """    DebugLogs(
        titleRes = Res.string.compose_settings_page_debug_logs,
        category = SettingsCategory.Advanced,
        parentPage = Advanced,
    ),
    PersistentSettings(
        titleRes = Res.string.compose_settings_page_persistent_settings,
        category = SettingsCategory.Advanced,
        parentPage = Advanced,
    ),
""",
)

screen = "composeApp/src/commonMain/kotlin/com/nuvio/app/features/settings/SettingsScreen.kt"
replace_once(
    screen,
    """                SettingsPage.Advanced -> advancedSettingsContent(
                    isTablet = false,
                    rememberLastProfileEnabled = rememberLastProfileEnabled,
                    onDebugLogsClick = { onPageChange(SettingsPage.DebugLogs) },
                )
                SettingsPage.DebugLogs -> debugLogsSettingsContent(
                    isTablet = false,
                )
""",
    """                SettingsPage.Advanced -> advancedSettingsContent(
                    isTablet = false,
                    rememberLastProfileEnabled = rememberLastProfileEnabled,
                    onPersistentSettingsClick = { onPageChange(SettingsPage.PersistentSettings) },
                    onDebugLogsClick = { onPageChange(SettingsPage.DebugLogs) },
                )
                SettingsPage.PersistentSettings -> persistentSettingsContent(
                    isTablet = false,
                )
                SettingsPage.DebugLogs -> debugLogsSettingsContent(
                    isTablet = false,
                )
""",
)
replace_once(
    screen,
    """                    SettingsPage.Advanced -> advancedSettingsContent(
                        isTablet = true,
                        rememberLastProfileEnabled = rememberLastProfileEnabled,
                        onDebugLogsClick = { openInlinePage(SettingsPage.DebugLogs) },
                    )
                    SettingsPage.DebugLogs -> debugLogsSettingsContent(
                        isTablet = true,
                    )
""",
    """                    SettingsPage.Advanced -> advancedSettingsContent(
                        isTablet = true,
                        rememberLastProfileEnabled = rememberLastProfileEnabled,
                        onPersistentSettingsClick = { openInlinePage(SettingsPage.PersistentSettings) },
                        onDebugLogsClick = { openInlinePage(SettingsPage.DebugLogs) },
                    )
                    SettingsPage.PersistentSettings -> persistentSettingsContent(
                        isTablet = true,
                    )
                    SettingsPage.DebugLogs -> debugLogsSettingsContent(
                        isTablet = true,
                    )
""",
)

strings = "composeApp/src/commonMain/composeResources/values/strings.xml"
strings_text = read(strings)
resource = '    <string name="compose_settings_page_persistent_settings">Persistent Settings</string>\n'
if "compose_settings_page_persistent_settings" not in strings_text:
    closing = "</resources>"
    if strings_text.count(closing) != 1:
        raise SystemExit("Could not find a unique </resources> anchor in strings.xml")
    strings_text = strings_text.replace(closing, resource + closing, 1)
    write(strings, strings_text)

print("Persistent Settings converted from dialog to native SettingsPage navigation.")
