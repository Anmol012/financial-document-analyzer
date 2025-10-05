import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import Header from './components/Header';
import { Toaster } from '@radix-ui/react-toast'; // Fix import
import { useState, useEffect } from 'react';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));

  useEffect(() => {
    const handleStorageChange = () => setIsAuthenticated(!!localStorage.getItem('token'));
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-background text-foreground dark">
        {isAuthenticated && <Header setIsAuthenticated={setIsAuthenticated} />}
        <main className="container mx-auto p-4">
          <Routes>
            <Route path="/login" element={isAuthenticated ? <Navigate to="/" /> : <Login setIsAuthenticated={setIsAuthenticated} />} />
            <Route path="/" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
            <Route path="/history" element={isAuthenticated ? <History /> : <Navigate to="/login" />} />
            <Route path="*" element={<div>404 - Page Not Found</div>} />
          </Routes>
        </main>
        <Toaster />
      </div>
    </Router>
  );
}

export default App;