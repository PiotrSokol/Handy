import React from "react";
import { ToggleSwitch } from "../ui/ToggleSwitch";
import { useSettings } from "../../hooks/useSettings";

interface AutostartProps {
  descriptionMode?: "inline" | "tooltip";
  grouped?: boolean;
}

export const Autostart: React.FC<AutostartProps> = React.memo(
  ({ descriptionMode = "tooltip", grouped = false }) => {
    const { getSetting, updateSetting, isUpdating } = useSettings();
    const value = getSetting("autostart_enabled") || false;

    return (
      <ToggleSwitch
        checked={value}
        onChange={(enabled) => updateSetting("autostart_enabled", enabled)}
        isUpdating={isUpdating("autostart_enabled")}
        label="Launch at Login"
        description="Start Handy automatically when you sign in"
        descriptionMode={descriptionMode}
        grouped={grouped}
      />
    );
  }
);

