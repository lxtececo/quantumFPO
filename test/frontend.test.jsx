import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../src/App.jsx';

// Mock Chart.js to avoid canvas issues in tests
jest.mock('react-chartjs-2', () => ({
  Pie: () => <div data-testid="pie-chart">Mock Pie Chart</div>,
  Scatter: () => <div data-testid="scatter-chart">Mock Scatter Chart</div>,
}));

describe('App Component Tests', () => {
  test('renders Quantum Portfolio Optimization heading', () => {
    render(<App />);
    const heading = screen.getByRole('heading', { name: /quantum portfolio optimization/i, level: 1 });
    expect(heading).toBeInTheDocument();
  });

  test('renders login form elements', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /login/i, level: 2 })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  test('login form accepts input', () => {
    render(<App />);
    const usernameInput = screen.getByPlaceholderText(/username/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'testpass' } });
    
    expect(usernameInput.value).toBe('testuser');
    expect(passwordInput.value).toBe('testpass');
  });

  test('shows error for invalid login', async () => {
    render(<App />);
    const usernameInput = screen.getByPlaceholderText(/username/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });
    
    fireEvent.change(usernameInput, { target: { value: 'wronguser' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpass' } });
    fireEvent.click(loginButton);
    
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });
});
