import React from 'react';
import InfoPane from './InfoPane'
import VideoPane from './VideoPane';
import './App.css';

function App() {
  return (
    <div className="App">
      <div className="info-pane"><InfoPane/></div>
      <div className="video-pane"><VideoPane/></div>
    </div>
  );
}

export default App;
