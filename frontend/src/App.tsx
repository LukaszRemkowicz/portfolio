import React, { Suspense, lazy } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import HomePage from "./HomePage";

// Lazy load larger components
const AstroGallery = lazy(() => import("./components/AstroGallery"));
const Programming = lazy(() => import("./components/Programming"));
const TravelHighlightsPage = lazy(
  () => import("./components/TravelHighlightsPage"),
);
import MainLayout from "./components/MainLayout";

import LoadingScreen from "./components/common/LoadingScreen";
import ScrollToHash from "./components/common/ScrollToHash";
import "./styles/components/App.module.css";

const App: React.FC = () => {
  return (
    <Router>
      <ScrollToHash />
      <Suspense fallback={<LoadingScreen />}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route
            path="/astrophotography"
            element={
              <MainLayout>
                <AstroGallery />
              </MainLayout>
            }
          />
          <Route
            path="/programming"
            element={
              <MainLayout>
                <Programming />
              </MainLayout>
            }
          />
          <Route
            path="/travel-highlights/:countrySlug/:placeSlug?"
            element={
              <MainLayout>
                <TravelHighlightsPage />
              </MainLayout>
            }
          />
        </Routes>
      </Suspense>
    </Router>
  );
};

export default App;
