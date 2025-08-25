import React from "react";
import { ToggleSwitch } from "../ui/ToggleSwitch";
import { useSettings } from "../../hooks/useSettings";

interface StartMinimizedProps {
  descriptionMode?: "inline" | "tooltip";
  grouped?: boolean;
}

export const StartMinimized: React.FC<StartMinimizedProps> = React.memo(
  ({ descriptionMode = "tooltip", grouped = false }) => {
    const { getSetting, updateSetting, isUpdating } = useSettings();
    const value = getSetting("start_minimized") || false;
    const autostartEnabled = getSetting("autostart_enabled") || false;

    return (
      <ToggleSwitch
        checked={value}
        onChange={(enabled) => updateSetting("start_minimized", enabled)}
        disabled={!autostartEnabled}
        isUpdating={isUpdating("start_minimized")}
        label="Start Minimized"
        description={
          autostartEnabled
            ? "Launch to the tray instead of showing the window"
            : "Enable Launch at Login to use Start Minimized"
        }
        descriptionMode={descriptionMode}
        grouped={grouped}
      />
    );
  }
);
