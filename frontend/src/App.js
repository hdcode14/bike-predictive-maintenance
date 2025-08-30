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
      const response = await axios.get('http://localhost:8000/predictions');
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

    try {
      const response = await axios.post('http://localhost:8000/plan_route', 
        Array.from(selectedBikes)
      );
      setRoute(response.data);
    } catch (error) {
      console.error('Error planning route:', error);
    }
  };

  const getRiskColor = (probability) => {
    if (probability > 0.7) return '#dc2626'; // red
    if (probability > 0.4) return '#ea580c'; // orange
    if (probability > 0.2) return '#ca8a04'; // yellow
    return '#16a34a'; // green
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
                    style={{ backgroundColor: getRiskColor(bike.failure_probability) }}
                  >
                    {(bike.failure_probability * 100).toFixed(1)}% risk
                  </span>
                </div>
                <div className="bike-details">
                  <span>{bike.total_km.toFixed(1)} km total</span>
                  <span>{bike.days_since_last_service} days since service</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="map-container">
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
                color={getRiskColor(bike.failure_probability)}
                onClick={() => toggleSelection(bike.bike_id)}
              />
            ))}
            
            {route && (
              <Source type="geojson" data={{
                type: 'Feature',
                geometry: route,
                properties: {}
              }}>
                <Layer
                  type="line"
                  layout={{ 'line-join': 'round', 'line-cap': 'round' }}
                  paint={{ 'line-color': '#007cbf', 'line-width': 4 }}
                />
              </Source>
            )}
          </Map>
        </div>
      </div>
    </div>
  );
}

export default App;