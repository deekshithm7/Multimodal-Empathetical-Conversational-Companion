import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useEmotionStore } from './store/useEmotionStore';
import { useAuthStore } from './store/useAuthStore';

// Routes & Pages (Barrel Import)
import {
  Login,
  Register,
  ForgotPassword,
  ResetPassword,
  Landing,
  Chat,
  Dashboard,
  History,
  Profile,
  Insights
} from './pages';

// Components (Barrel Import)
import {
  ProtectedRoute,
  PublicRoute,
  TopNav,
  MobileTabNav,
  ToastContainer
} from './components';

function App() {
  const { currentEmotion } = useEmotionStore();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    // Update CSS variables for Dark Therapeutic Theme
    const root = document.documentElement;
    switch (currentEmotion) {
      case 'happy': root.style.setProperty('--theme-bg', '#1a1612'); break; // Warm Amber Dark
      case 'sad': root.style.setProperty('--theme-bg', '#0f131a'); break; // Deep Blue Dark
      case 'angry': root.style.setProperty('--theme-bg', '#1a1010'); break; // Deep Red Dark
      default: root.style.setProperty('--theme-bg', '#0a0a0c'); // Void
    }
  }, [currentEmotion]);

  return (
    <Router>
      <div className="h-screen w-screen overflow-hidden relative bg-[var(--theme-bg)] transition-colors duration-[4000ms] text-slate-200 font-sans">

        {/* Navigation - Only show when authenticated */}
        {isAuthenticated && <TopNav />}

        {/* Main Content Area */}
        <main className={`w-full ${isAuthenticated ? 'h-[calc(100vh-64px)]' : 'h-screen'} overflow-y-auto relative`}>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Landing />} />

            <Route path="/login" element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            } />

            <Route path="/register" element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            } />

            <Route path="/forgot-password" element={
              <PublicRoute>
                <ForgotPassword />
              </PublicRoute>
            } />

            <Route path="/reset-password" element={
              <PublicRoute>
                <ResetPassword />
              </PublicRoute>
            } />

            {/* Protected Routes */}
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />

            <Route path="/chat" element={
              <ProtectedRoute>
                <Chat />
              </ProtectedRoute>
            } />

            <Route path="/history" element={
              <ProtectedRoute>
                <History />
              </ProtectedRoute>
            } />

            <Route path="/profile" element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            } />

            <Route path="/insights" element={
              <ProtectedRoute>
                <Insights />
              </ProtectedRoute>
            } />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        {/* Mobile Navigation - Only show when authenticated */}
        {isAuthenticated && <MobileTabNav />}

        {/* Global Toast Container */}
        <ToastContainer />
      </div>
    </Router>
  );
}

export default App;
