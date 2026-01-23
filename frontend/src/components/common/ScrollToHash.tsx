import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const ScrollToHash = () => {
  const { hash } = useLocation();

  useEffect(() => {
    if (hash) {
      const element = document.getElementById(hash.replace('#', ''));
      if (element) {
        // Add a small delay to ensure DOM is fully rendered (especially with lazy loading)
        setTimeout(() => {
          element.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    } else {
      // Optional: Scroll to top if no hash (unless we want to preserve scroll on back nav)
      window.scrollTo(0, 0);
    }
  }, [hash]);

  return null;
};

export default ScrollToHash;
