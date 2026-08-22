import React from 'react';
import { render, screen } from '@testing-library/react';
import Navbar from '../Navbar';

describe('Navbar', () => {
  it('renders brand name and projects link', () => {
    render(<Navbar />);
    expect(screen.getByText(/Molecule to Market AI/i)).toBeInTheDocument();
    expect(screen.getByText(/Projects Hub/i)).toBeInTheDocument();
  });

  it('shows active initiative when props provided', () => {
    render(<Navbar projectTitle="Test Project" moleculeName="MolX" />);
    expect(screen.getByText(/Active Initiative/i)).toBeInTheDocument();
    expect(screen.getByText(/Test Project/i)).toBeInTheDocument();
    expect(screen.getByText(/MolX/i)).toBeInTheDocument();
  });
});
