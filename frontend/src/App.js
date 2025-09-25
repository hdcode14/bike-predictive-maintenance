import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Map from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import './App.css';

// ADD YOUR MAPBOX TOKEN DIRECTLY HERE
const MAPBOX_TOKEN = 'pk.eyJ1IjoiaHJpc2loZCIsImEiOiJjbWV5OHV5aGsxZzJrMnJvYXV2NjIzM2FmIn0.EkiCK9FTrUSSYgISQY41Vg';

function App() {
  const [bikes, setBikes] = useState([]);
  const [selectedBikes, setSelectedBikes] = useState(new Set());
  const [viewState, setViewState] = useState({
    longitude: -74.006,
    latitude: 40.7128,
    zoom: 12
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = async () => {
    try {
      setLoading(true);
      // Try to connect to backend with timeout
      const response = await axios.get('http://localhost:8000/predictions', {
        timeout: 3000
      });
      setBikes(response.data);
      setError(null);
    } catch (error) {
      console.log('Backend not available, using demo data');
      setError('Failed to connect to backend. Using demo data.');
      setBikes(generateMockData());
    } finally {
      setLoading(false);
    }
  };

  const generateMockData = () => {
    const priorities = ['high', 'medium', 'low'];
    const issues = {
      high: ['brake failure', 'chain broken', 'tire puncture'],
      medium: ['brake pads worn', 'chain rust', 'tire wear'],
      low: ['general maintenance', 'cleaning needed', 'lubrication']
    };
    
    return Array.from({ length: 15 }, (_, i) => {
      const priority = priorities[i % 3];
      return {
        bike_id: i + 1,
        maintenance_priority: priority,
        predicted_issues: issues[priority],
        total_distance_km: Math.random() * 200 + 50,
        last_service: `${Math.floor(Math.random() * 30) + 1} days ago`,
        confidence_score: Math.random() * 0.3 + 0.7
      };
    });
  };

  const toggleSelection = (bikeId) => {
    const newSelection = new Set(selectedBikes);
    if (newSelection.has(bikeId)) {
      newSelection.delete(bikeId);
    } else {
      newSelection.add(bikeId);
    }
    setSelectedBikes(newSelection);
  };

  const planRoute = async () => {
    if (selectedBikes.size === 0) return;
    alert(`Route planning for bikes: ${Array.from(selectedBikes).join(', ')}\n(Note: Route planning endpoint not implemented yet)`);
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return '#dc2626';
      case 'medium': return '#ea580c';
      case 'low': return '#16a34a';
      default: return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div className="App">
        <div className="loading">Loading bike data...</div>
      </div>
    );
  }

  return (
    <div className="App">
      <div className="dashboard">
        <div className="sidebar">
          <h1>🚴 Bike Maintenance Dashboard</h1>
          
          {error && (
            <div className="error-banner">
              ⚠️ {error}
            </div>
          )}
          
          <button 
            onClick={planRoute} 
            disabled={selectedBikes.size === 0}
            className="route-button"
          >
            🗺️ Plan Route ({selectedBikes.size} selected)
          </button>
          
          <div className="bike-list">
            <h2>Maintenance Priority</h2>
            {bikes.map(bike => (
              <div 
                key={bike.bike_id} 
                className={`bike-item ${selectedBikes.has(bike.bike_id) ? 'selected' : ''}`}
                onClick={() => toggleSelection(bike.bike_id)}
              >
                <div className="bike-header">
                  <span className="bike-id">Bike #{bike.bike_id}</span>
                  <span 
                    className="risk-badge"
                    style={{ backgroundColor: getPriorityColor(bike.maintenance_priority) }}
                  >
                    {bike.maintenance_priority.toUpperCase()}
                  </span>
                </div>
                <div className="bike-details">
                  <span>{bike.total_distance_km?.toFixed(1) || '0'} km total</span>
                  <span>Last: {bike.last_service || 'Unknown'}</span>
                  <span>Issues: {Array.isArray(bike.predicted_issues) ? bike.predicted_issues.join(', ') : 'None'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="map-container">
          {/* Fixed Map Component for v7.1.4 */}
          <Map
            {...viewState}
            onViewportChange={setViewState}
            mapboxApiAccessToken={MAPBOX_TOKEN}
            mapStyle="mapbox://styles/mapbox/streets-v11"
            onLoad={() => {
              console.log('Map loaded successfully!');
              setMapLoaded(true);
            }}
            style={{ width: '100%', height: '100%' }}
          >
            {bikes.map(bike => (
              <Map.Marker
                key={bike.bike_id}
                longitude={-74.006 + (bike.bike_id % 10) * 0.01}
                latitude={40.7128 + (bike.bike_id % 10) * 0.01}
              >
                <div 
                  style={{
                    backgroundColor: getPriorityColor(bike.maintenance_priority),
                    width: '20px',
                    height: '20px',
                    borderRadius: '50%',
                    cursor: 'pointer',
                    border: selectedBikes.has(bike.bike_id) ? '3px solid white' : '2px solid black'
                  }}
                  onClick={() => toggleSelection(bike.bike_id)}
                />
              </Map.Marker>
            ))}
          </Map>
          
          {/* Debug Info */}
          <div style={{
            position: 'absolute',
            top: '10px',
            right: '10px',
            background: 'rgba(0,0,0,0.9)',
            color: 'white',
            padding: '15px',
            zIndex: 1000,
            borderRadius: '8px',
            fontSize: '12px'
          }}>
            <div>🗺️ Map Status: {mapLoaded ? 'LOADED' : 'LOADING...'}</div>
            <div>📍 {viewState.longitude.toFixed(4)}, {viewState.latitude.toFixed(4)}</div>
            <div>🔑 Token: {MAPBOX_TOKEN ? 'SET' : 'MISSING'}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;