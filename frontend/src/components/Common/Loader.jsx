import React from 'react';
import './Common.css';

export const Loader = ({ size = 'medium', message }) => {
  return (
    <div className="loader-container">
      <div className={`spinner ${size}`}></div>
      {message && <p className="loader-message">{message}</p>}
    </div>
  );
};
export default Loader;
