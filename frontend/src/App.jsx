import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import Instances from './components/Instances';
import Logs from './components/Logs';
import Backups from './components/Backups';
import BackupsV2 from './components/BackupsV2';
import Layout from './components/Layout';

function PrivateRoute({ children }) {
  const token = localStorage.getItem('access_token');
  return token ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/instances"
          element={
            <PrivateRoute>
              <Layout>
                <Instances />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/logs"
          element={
            <PrivateRoute>
              <Layout>
                <Logs />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/backups"
          element={
            <PrivateRoute>
              <Layout>
                <Backups />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/backups-v2"
          element={
            <PrivateRoute>
              <Layout>
                <BackupsV2 />
              </Layout>
            </PrivateRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
