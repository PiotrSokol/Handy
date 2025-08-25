# Autostart Toggle Implementation Suggestions

## 1. Update AppSettings Structure

**File: `src/settings.rs`**

Add the autostart field to the `AppSettings` struct:

```rust
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct AppSettings {
    pub bindings: HashMap<String, ShortcutBinding>,
    pub push_to_talk: bool,
    pub audio_feedback: bool,
    #[serde(default = "default_start_minimized")]
    pub start_minimized: bool,
    #[serde(default = "default_model")]
    pub selected_model: String,
    #[serde(default = "default_always_on_microphone")]
    pub always_on_microphone: bool,
    #[serde(default)]
    pub selected_microphone: Option<String>,
    #[serde(default)]
    pub selected_output_device: Option<String>,
    #[serde(default = "default_translate_to_english")]
    pub translate_to_english: bool,
    #[serde(default = "default_selected_language")]
    pub selected_language: String,
    #[serde(default = "default_overlay_position")]
    pub overlay_position: OverlayPosition,
    #[serde(default = "default_debug_mode")]
    pub debug_mode: bool,
    #[serde(default)]
    pub custom_words: Vec<String>,
    #[serde(default = "default_word_correction_threshold")]
    pub word_correction_threshold: f64,
    // NEW FIELD:
    #[serde(default = "default_autostart_enabled")]
    pub autostart_enabled: bool,
}

// ADD THIS DEFAULT FUNCTION:
fn default_autostart_enabled() -> bool {
    false
}
```

**Update the `get_default_settings()` function:**

```rust
pub fn get_default_settings() -> AppSettings {
    // ... existing code ...

    AppSettings {
        bindings,
        push_to_talk: true,
        audio_feedback: false,
        start_minimized: false,
        selected_model: "".to_string(),
        always_on_microphone: false,
        selected_microphone: None,
        selected_output_device: None,
        translate_to_english: false,
        selected_language: "auto".to_string(),
        overlay_position: OverlayPosition::Bottom,
        debug_mode: false,
        custom_words: Vec::new(),
        word_correction_threshold: default_word_correction_threshold(),
        // ADD THIS:
        autostart_enabled: false,
    }
}
```

## 2. Add Autostart Command

**File: `src/shortcut.rs`**

Add this new command following the existing pattern:

```rust
#[tauri::command]
pub fn change_autostart_setting(app: AppHandle, enabled: bool) -> Result<(), String> {
    let mut settings = settings::get_settings(&app);
    settings.autostart_enabled = enabled;
    settings::write_settings(&app, settings);

    // Apply the autostart change immediately
    let autostart_manager = app.autolaunch();
    if enabled {
        autostart_manager.enable().map_err(|e| e.to_string())?;
    } else {
        autostart_manager.disable().map_err(|e| e.to_string())?;
    }

    Ok(())
}
```

## 3. Update Initialization Logic

**File: `src/lib.rs`**

In the `setup` closure, replace the hardcoded autostart with settings-based logic:

**REMOVE this line:**
```rust
// Get the autostart manager
let autostart_manager = app.autolaunch();
// Enable autostart
let _ = autostart_manager.enable();
```

**REPLACE with:**
```rust
// Apply autostart setting from user preferences
let settings = settings::get_settings(&app.handle());
let autostart_manager = app.autolaunch();
if settings.autostart_enabled {
    let _ = autostart_manager.enable();
} else {
    let _ = autostart_manager.disable();
}
```

## 4. Register New Command

**File: `src/lib.rs`**

Add the new command to the `invoke_handler`:

```rust
.invoke_handler(tauri::generate_handler![
    shortcut::change_binding,
    shortcut::reset_binding,
    shortcut::change_ptt_setting,
    shortcut::change_audio_feedback_setting,
    shortcut::change_start_minimized_setting,
    shortcut::change_translate_to_english_setting,
    shortcut::change_selected_language_setting,
    shortcut::change_overlay_position_setting,
    shortcut::change_debug_mode_setting,
    shortcut::change_word_correction_threshold_setting,
    shortcut::update_custom_words,
    shortcut::suspend_binding,
    shortcut::resume_binding,
    // ADD THIS NEW COMMAND:
    shortcut::change_autostart_setting,
    trigger_update_check,
    // ... rest of existing commands ...
])
```

## 5. Update Permissions

**File: `capabilities/default.json`**

Ensure autostart permissions are included:

```json
{
  "permissions": [
    "autostart:allow-enable",
    "autostart:allow-disable", 
    "autostart:allow-is-enabled"
  ]
}
```

## 6. Frontend Usage

The frontend can now control autostart with:

```typescript
import { invoke } from '@tauri-apps/api/core';

// Enable autostart
await invoke('change_autostart_setting', { enabled: true });

// Disable autostart
await invoke('change_autostart_setting', { enabled: false });
```

## Implementation Notes

- This follows your existing pattern of `change_*_setting` commands
- Settings are automatically persisted using your existing store system
- Autostart changes are applied immediately when the setting is toggled
- The `--hidden` flag will still be passed when the app autostarts (from existing configuration)
- Backward compatibility is maintained with `#[serde(default)]` attributes
