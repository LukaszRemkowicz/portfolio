import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

const ScrollToHash = () => {
  const { hash, pathname } = useLocation();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const observerRef = useRef<MutationObserver | null>(null);

  useEffect(() => {
    // Prevent browser from restoring scroll position automatically when navigating
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }

    // Clean up previous checks
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (observerRef.current) {
      observerRef.current.disconnect();
      observerRef.current = null;
    }

    if (!hash) {
      window.scrollTo(0, 0);
      return;
    }

    const elementId = hash.replace('#', '');

    const tryScroll = () => {
      const element = document.getElementById(elementId);
      if (element) {
        // Double requestAnimationFrame to ensure we're in the next paint cycle
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            // We use 'auto' for instant jump during loading phase to prevent visible scrolling artifacts
            // when multiple layout shifts happen
            element.scrollIntoView({ behavior: 'auto', block: 'start' });
          });
        });
        return true;
      }
      return false;
    };

    // Attempt immediately
    tryScroll();

    // Observe DOM changes to handle lazy loaded content and layout shifts
    const observer = new MutationObserver(() => {
      tryScroll();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true, // Also watch for attribute changes that might affect layout
    });
    observerRef.current = observer;

    // Keep observing for a window of time to ensure we catch all lazy loads
    // 2.5 seconds should be enough for most content to settle
    timeoutRef.current = setTimeout(() => {
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
      }
    }, 2500);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (observerRef.current) observerRef.current.disconnect();
    };
  }, [hash, pathname]);

  return null;
};

export default ScrollToHash;
