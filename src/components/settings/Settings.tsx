import React, { useEffect, useState } from "react";
import { MicrophoneSelector } from "./MicrophoneSelector";
import { AlwaysOnMicrophone } from "./AlwaysOnMicrophone";
import { PushToTalk } from "./PushToTalk";
import { AudioFeedback } from "./AudioFeedback";
import { OutputDeviceSelector } from "./OutputDeviceSelector";
import { ShowOverlay } from "./ShowOverlay";
import { HandyShortcut } from "./HandyShortcut";
import { TranslateToEnglish } from "./TranslateToEnglish";
import { LanguageSelector } from "./LanguageSelector";
import { CustomWords } from "./CustomWords";
import { SettingsGroup } from "../ui/SettingsGroup";
import { WordCorrectionThreshold } from "./debug/WordCorrectionThreshold";
import { AppDataDirectory } from "./AppDataDirectory";
import { StartMinimized } from "./StartMinimized";
import { Autostart } from "./Autostart";
import { useSettings } from "../../hooks/useSettings";

export const Settings: React.FC = () => {
  const { settings, updateSetting } = useSettings();
  const [isDesktop, setIsDesktop] = useState(true);

  useEffect(() => {
    // Determine if running in Tauri (desktop). In web preview, this is undefined.
    const isTauri = typeof (window as any).__TAURI__ !== "undefined";
    setIsDesktop(isTauri);
  }, []);

  // Handle keyboard shortcuts for debug mode toggle
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check for Ctrl+Shift+D (Windows/Linux) or Cmd+Shift+D (macOS)
      const isDebugShortcut =
        event.shiftKey &&
        event.key.toLowerCase() === "d" &&
        (event.ctrlKey || event.metaKey);

      if (isDebugShortcut) {
        event.preventDefault();
        const currentDebugMode = settings?.debug_mode ?? false;
        updateSetting("debug_mode", !currentDebugMode);
      }
    };

    // Add event listener when component mounts
    document.addEventListener("keydown", handleKeyDown);

    // Cleanup event listener when component unmounts
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [settings?.debug_mode, updateSetting]);

  return (
    <div className="max-w-3xl w-full mx-auto space-y-6">
      <SettingsGroup>
        {isDesktop && (
          <HandyShortcut descriptionMode="tooltip" grouped={true} />
        )}
        {isDesktop && (
          <>
            <Autostart descriptionMode="tooltip" grouped={true} />
            <StartMinimized descriptionMode="tooltip" grouped={true} />
          </>
        )}
        <MicrophoneSelector descriptionMode="tooltip" grouped={true} />
        <LanguageSelector descriptionMode="tooltip" grouped={true} />
      </SettingsGroup>

      <SettingsGroup title="Advanced">
        <PushToTalk descriptionMode="tooltip" grouped={true} />
        <AudioFeedback descriptionMode="tooltip" grouped={true} />
        <OutputDeviceSelector descriptionMode="tooltip" grouped={true} />
        <ShowOverlay descriptionMode="tooltip" grouped={true} />
        <TranslateToEnglish descriptionMode="tooltip" grouped={true} />
        <CustomWords descriptionMode="tooltip" grouped />
        <AlwaysOnMicrophone descriptionMode="tooltip" grouped={true} />
      </SettingsGroup>

      {settings?.debug_mode && (
        <SettingsGroup title="Debug">
          <WordCorrectionThreshold descriptionMode="tooltip" grouped={true} />
          <AppDataDirectory descriptionMode="tooltip" grouped={true} />
        </SettingsGroup>
      )}
    </div>
  );
};
