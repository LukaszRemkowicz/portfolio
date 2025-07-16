import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './HomePage';
import AstroGallery from './AstroGallery';
import MainLayout from './MainLayout';
import './App.module.css';

const App = () => {
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
      </Routes>
    </Router>
  );
};

export default App;