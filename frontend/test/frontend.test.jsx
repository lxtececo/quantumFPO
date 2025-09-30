import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../src/App.jsx';

// Mock Chart.js to avoid canvas issues in tests
jest.mock('react-chartjs-2', () => ({
  Pie: () => <div data-testid="pie-chart">Mock Pie Chart</div>,
  Scatter: () => <div data-testid="scatter-chart">Mock Scatter Chart</div>,
  Line: () => <div data-testid="line-chart">Mock Line Chart</div>,
}));

// Mock BlochSpinner component to avoid SVG/animation issues in tests
jest.mock('../src/components/BlochSpinner', () => {
  return function MockBlochSpinner({ className, ariaLabel, ...props }) {
    return (
      <div 
        data-testid="bloch-spinner" 
        className={className}
        aria-label={ariaLabel || 'Loading spinner'}
        {...props}
      >
        Mock Bloch Spinner
      </div>
    );
  };
});

describe('App Component Tests', () => {
  test('renders quantumFPO heading', () => {
    render(<App />);
    const heading = screen.getByRole('heading', { name: /quantumfpo/i, level: 1 });
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
    
    // Check for loading state (button should show spinner briefly)
    await waitFor(() => {
      // The button text changes to "Authenticating..." during loading
      expect(loginButton).toBeDisabled();
    }, { timeout: 1000 });
    
    // Check for error message after loading
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test('shows loading spinner during authentication', async () => {
    render(<App />);
    const usernameInput = screen.getByPlaceholderText(/username/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });
    
    fireEvent.change(usernameInput, { target: { value: 'demo' } });
    fireEvent.change(passwordInput, { target: { value: 'quantum123' } });
    fireEvent.click(loginButton);
    
    // Should show loading state with both inline and fixed spinners
    await waitFor(() => {
      const spinners = screen.getAllByTestId('bloch-spinner');
      expect(spinners).toHaveLength(2); // inline + fixed position
      
      // Check inline spinner in button
      const inlineSpinner = spinners.find(spinner => 
        spinner.classList.contains('inline-spinner')
      );
      expect(inlineSpinner).toBeInTheDocument();
      
      // Check fixed position spinner
      const fixedSpinner = spinners.find(spinner => 
        spinner.classList.contains('bloch-spinner-fixed')
      );
      expect(fixedSpinner).toBeInTheDocument();
    }, { timeout: 500 });
  });

  test('successful login hides login form', async () => {
    render(<App />);
    const usernameInput = screen.getByPlaceholderText(/username/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });
    
    fireEvent.change(usernameInput, { target: { value: 'demo' } });
    fireEvent.change(passwordInput, { target: { value: 'quantum123' } });
    fireEvent.click(loginButton);
    
    // Wait for login to complete and portfolio form to appear
    await waitFor(() => {
      expect(screen.getByText(/load stocks for portfolio/i)).toBeInTheDocument();
    }, { timeout: 3000 });
    
    // Login form should no longer be visible
    expect(screen.queryByText(/sample user/i)).not.toBeInTheDocument();
  });
});
