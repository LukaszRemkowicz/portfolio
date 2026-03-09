import { useState, ImgHTMLAttributes } from 'react';

interface ImageWithFallbackProps extends ImgHTMLAttributes<HTMLImageElement> {
  fallbackSrc?: string;
}

const ImageWithFallback = ({
  src,
  fallbackSrc = '/landscape.png',
  alt,
  className,
  onLoad,
  onError,
  ...props
}: ImageWithFallbackProps) => {
  const [hasError, setHasError] = useState(!src);

  const handleError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    if (!hasError) {
      setHasError(true);
    }
    if (onError) {
      onError(e);
    }
  };

  return (
    <img
      {...props}
      src={hasError || !src ? fallbackSrc : src}
      alt={alt}
      className={className}
      onLoad={onLoad}
      onError={handleError}
    />
  );
};

export default ImageWithFallback;
