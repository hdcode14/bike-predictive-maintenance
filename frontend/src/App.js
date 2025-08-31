// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Map, { Marker, Source, Layer } from 'react-map-gl/mapbox';
import 'mapbox-gl/dist/mapbox-gl.css';
import './App.css';

const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;

function App() {
  const [bikes, setBikes] = useState([]);
  const [selectedBikes, setSelectedBikes] = useState(new Set());
  const [route, setRoute] = useState(null);
  const [viewState, setViewState] = useState({
    longitude: -74.006,
    latitude: 40.7128,
    zoom: 12
  });

  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = async () => {
    try {
      const response = await axios.get('/predictions');
      setBikes(response.data);
    } catch (error) {
      console.error('Error fetching predictions:', error);
    }
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
      case 'high': return '#dc2626'; // red
      case 'medium': return '#ea580c'; // orange
      case 'low': return '#16a34a'; // green
      default: return '#6b7280'; // gray
    }
  };

  // Calculate failure probability based on maintenance priority
  const getFailureProbability = (priority) => {
    switch (priority) {
      case 'high': return 0.85;
      case 'medium': return 0.55;
      case 'low': return 0.25;
      default: return 0.1;
    }
  };

  return (
    <div className="App">
      <div className="dashboard">
        <div className="sidebar">
          <h1>🚴 Bike Maintenance Dashboard</h1>
          <button 
            onClick={planRoute} 
            disabled={selectedBikes.size === 0}
            className="route-button"
          >
            🗺️ Plan Route ({selectedBikes.size} selected)
          </button>
          
          <div className="bike-list">
            <h2>Maintenance Priority</h2>
            {bikes.length === 0 ? (
              <p>Loading bike predictions...</p>
            ) : (
              bikes.map(bike => {
                const failureProbability = getFailureProbability(bike.maintenance_priority);
                return (
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
                      <span>{bike.total_distance_km.toFixed(1)} km total</span>
                      <span>Last service: {bike.last_service}</span>
                      <span>Issues: {bike.predicted_issues.join(', ')}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div className="map-container">
          {MAPBOX_TOKEN ? (
            <Map
              {...viewState}
              onMove={evt => setViewState(evt.viewState)}
              mapboxAccessToken={MAPBOX_TOKEN}
              style={{ width: '100%', height: '100%' }}
              mapStyle="mapbox://styles/mapbox/streets-v11"
            >
              {bikes.map(bike => (
                <Marker
                  key={bike.bike_id}
                  longitude={-74.006 + (bike.bike_id % 10) * 0.01}
                  latitude={40.7128 + (bike.bike_id % 10) * 0.01}
                  color={getPriorityColor(bike.maintenance_priority)}
                  onClick={() => toggleSelection(bike.bike_id)}
                />
              ))}
            </Map>
          ) : (
            <div className="map-placeholder">
              <h3>Map Configuration Required</h3>
              <p>Please add your Mapbox access token to the JavaScript code.</p>
              <p>Get your token at <a href="https://mapbox.com" target="_blank" rel="noopener noreferrer">mapbox.com</a></p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;