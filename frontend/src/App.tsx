import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import HomePage from "./HomePage";
import AstroGallery from "./components/AstroGallery";
import Programming from "./components/Programming";
import MainLayout from "./components/MainLayout";
import "./styles/components/App.module.css";

const App: React.FC = () => {
  return (
    <Router>
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
      </Routes>
    </Router>
  );
};

export default App;
