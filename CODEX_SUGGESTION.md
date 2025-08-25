# Plan: Remove CLI args; drive autostart + visibility from settings

## Objectives
- Eliminate any dependency on process CLI flags (e.g., `--hidden`).
- Control autostart enablement and startup visibility strictly via persisted user settings.
- Keep behavior consistent across platforms without detecting “autostart vs manual” launches.

## Scope
- Rust (Tauri) code only, plus a small UI hook to toggle the new setting.
- No change to feature semantics other than removing CLI flag dependency and adding a user-facing autostart toggle.

## Proposed Settings Model
- `start_minimized: bool` (existing): When true, always hide main window on startup (manual and autostart).
- `autostart_enabled: bool` (new): When true, register the app with the OS to launch at login; otherwise disable.
- Defaults: `start_minimized = false`; `autostart_enabled = false` (privacy-friendly explicit opt-in).

## Changes by File

### src-tauri/src/lib.rs
1. Autostart plugin init without args
   - Replace: `tauri_plugin_autostart::init(MacosLauncher::LaunchAgent, Some(vec!["--hidden".into()]))`
   - With:    `tauri_plugin_autostart::init(MacosLauncher::LaunchAgent, None)`
2. Read settings in `setup` once:
   - `let settings = settings::get_settings(&app.handle());`
   - `let start_hidden = settings.start_minimized;`
   - `let auto_enabled = settings.autostart_enabled;`
3. Apply startup visibility uniformly (independent of launch source):
   - If `start_hidden`, hide main window and on macOS set `ActivationPolicy::Accessory`.
4. Apply autostart state from setting:
   - `let manager = app.autolaunch();`
   - `if auto_enabled { let _ = manager.enable(); } else { let _ = manager.disable(); }`
5. Remove any logic related to CLI args; do not parse or react to flags.

### src-tauri/src/settings.rs
1. Extend `AppSettings`:
   - Add `#[serde(default = "default_autostart_enabled")] pub autostart_enabled: bool,`
   - Implement `fn default_autostart_enabled() -> bool { false }`
2. Include in `get_default_settings()` with `autostart_enabled: false`.
3. Store accessors unchanged; field persists alongside others in `settings_store.json`.
4. Optional migration nicety: On first run after this change (i.e., if `autostart_enabled` missing in store), try to infer initial value:
   - If the plugin exposes a query (e.g., `app.autolaunch().is_enabled()`), use it; otherwise default to `false`.
   - Persist the inferred value once to avoid repeated checks.

### src-tauri/src/shortcut.rs
1. New Tauri command to toggle autostart:
   - `#[tauri::command] pub fn change_autostart_enabled_setting(app: AppHandle, enabled: bool) -> Result<(), String>`
   - Update settings: `settings.autostart_enabled = enabled; settings::write_settings(&app, settings);`
   - Immediately apply: `if enabled { app.autolaunch().enable() } else { app.autolaunch().disable() }` (ignore errors, log best-effort).
2. Keep existing `change_start_minimized_setting` as-is.
3. Register the new command in `lib.rs` `invoke_handler`.

### Frontend (minimal wiring)
- Add/keep UI toggles:
  - “Launch at login” → calls `change_autostart_enabled_setting({ enabled })`.
  - “Start minimized” → calls `change_start_minimized_setting({ enabled })`.
- Read/reflect both from the store-backed settings endpoint already in use by the app.

## Behavioral Notes
- Startup visibility applies to all launches; we do not differentiate autostart vs manual to avoid platform-specific detection and reintroducing flags.
- Autostart enablement is applied both at startup and when toggled at runtime for immediate effect.

## Migration Strategy
- Backward compatibility: Existing users previously had autostart enabled unconditionally. Options:
  1) Conservative (recommended): default `autostart_enabled = false` and show the toggle; users opt in explicitly.
  2) Heuristic: if API exists to check current autostart registration, infer true/false on first run and persist.
- No data loss: settings struct change is additive with serde defaults.

## Testing & QA Checklist
- Fresh install: defaults show autostart off, start minimized off; app shows on first launch; login items/autorun entry not created.
- Toggle autostart on: verify OS login item/autorun is created; restart OS session → app launches.
- Toggle autostart off: verify login item/autorun removed; restart OS session → app does not launch.
- Toggle start minimized on: relaunch app manually → main window starts hidden; macOS activation policy set to Accessory.
- Toggle start minimized off: relaunch app manually → main window visible.
- Combined: autostart on + start minimized on → after login, app runs hidden.
- Combined: autostart on + start minimized off → after login, app runs visible.
- Cross-platform smoke: macOS (LaunchAgent), Windows (Registry), Linux (desktop file) — plugin handles specifics.

## Out of Scope
- Detecting autostart vs manual launch; no CLI flags or platform heuristics.
- Changing other settings semantics or unrelated features.

## Rollback Plan
- If issues arise, revert to previous autostart init with args and unconditional enable in `lib.rs`.
- Reverting does not corrupt user settings; extra `autostart_enabled` will be ignored safely.

## Future Improvements (optional)
- Rename `start_minimized` → `start_hidden` for clarity (with serde alias for backward compatibility).
- Surface autostart status readback in UI by querying plugin state (if exposed) for better UX on migration.
