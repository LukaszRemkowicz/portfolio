import { act, renderHook } from '@testing-library/react';
import {
  useHeroImageVariantSize,
  useImageVariantSize,
} from '../../hooks/useImageVariantSize';

const setViewportWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', {
    configurable: true,
    value: width,
  });
};

describe('useImageVariantSize', () => {
  it('updates card image size when the viewport changes', () => {
    setViewportWidth(1280);

    const { result } = renderHook(() => useImageVariantSize());

    expect(result.current).toBe(840);

    act(() => {
      setViewportWidth(500);
      window.dispatchEvent(new Event('resize'));
    });

    expect(result.current).toBe(320);
  });

  it('updates hero image size when the viewport changes', () => {
    setViewportWidth(1280);

    const { result } = renderHook(() => useHeroImageVariantSize());

    expect(result.current).toBe(1920);

    act(() => {
      setViewportWidth(1800);
      window.dispatchEvent(new Event('resize'));
    });

    expect(result.current).toBe(2560);
  });
});
