import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

// Import components (will create these in subsequent phases)
const LandingPage = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <h1 className="text-4xl font-bold text-gray-800 mb-4">
        Welcome to <span className="text-primary">Aman</span>
      </h1>
      <p className="text-xl text-gray-600 mb-8">
        Cybersecurity Platform - Protecting SMEs from Phishing Attacks
      </p>
      <div className="bg-primary text-black px-6 py-3 rounded-lg font-semibold">
        Phase 1 Complete ✅
      </div>
    </div>
  </div>
);

const Dashboard = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <h1 className="text-3xl font-bold text-gray-800 mb-4">Dashboard</h1>
      <p className="text-gray-600">Coming in Phase 3</p>
    </div>
  </div>
);

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;