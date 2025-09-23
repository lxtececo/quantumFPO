

import '@testing-library/jest-dom';
import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../src/App';

describe('App Component', () => {
  test('renders main header', () => {
    render(<App />);
    expect(screen.getByText(/portfolio/i)).toBeInTheDocument();
  });
});
