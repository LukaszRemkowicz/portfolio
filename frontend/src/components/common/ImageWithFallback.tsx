import { useEffect, useRef, useState, ImgHTMLAttributes } from 'react';

interface ImageWithFallbackProps extends ImgHTMLAttributes<HTMLImageElement> {
  fallbackSrc?: string;
  fallbackOnEmptySrc?: boolean;
}

const ImageWithFallback = ({
  src,
  fallbackSrc = '/landscape.webp',
  fallbackOnEmptySrc = true,
  alt,
  className,
  onLoad,
  onError,
  ...props
}: ImageWithFallbackProps) => {
  const [failedSrc, setFailedSrc] = useState<string | null>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);
  const resolvedSrc =
    failedSrc === src
      ? fallbackSrc
      : src || (fallbackOnEmptySrc ? fallbackSrc : undefined);

  useEffect(() => {
    const img = imgRef.current;
    if (!img || !img.complete) return;

    if (img.naturalWidth > 0) {
      onLoad?.({
        currentTarget: img,
        target: img,
      } as unknown as React.SyntheticEvent<HTMLImageElement, Event>);
      return;
    }

    if (src && failedSrc !== src) {
      queueMicrotask(() => {
        setFailedSrc(currentFailedSrc =>
          currentFailedSrc === src ? currentFailedSrc : src
        );
      });
    }
  }, [resolvedSrc, failedSrc, onLoad, src]);

  const handleError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    if (src && failedSrc !== src) {
      setFailedSrc(src);
    }
    if (onError) {
      onError(e);
    }
  };

  return (
    <img
      ref={imgRef}
      {...props}
      src={resolvedSrc}
      alt={alt}
      className={className}
      onLoad={onLoad}
      onError={handleError}
    />
  );
};

export default ImageWithFallback;
