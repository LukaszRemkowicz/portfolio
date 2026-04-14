import { useSettings } from './useSettings';
import { EnabledFeatures } from '../types';

export type FeatureFlagName = 'shop' | 'programming';

export const isFeatureEnabled = (
  settings: EnabledFeatures | undefined,
  feature: FeatureFlagName
): boolean => settings?.[feature] === true;

export const useFeatureFlags = () => {
  const { data: settings, isLoading } = useSettings();

  return {
    settings,
    isLoading,
    isEnabled: (feature: FeatureFlagName) =>
      isFeatureEnabled(settings, feature),
  };
};

export const useFeatureFlag = (feature: FeatureFlagName) => {
  const { settings, isLoading, isEnabled } = useFeatureFlags();

  return {
    settings,
    isLoading,
    isEnabled: isEnabled(feature),
  };
};
