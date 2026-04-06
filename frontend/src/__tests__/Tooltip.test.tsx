import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

import Tooltip from '../components/common/Tooltip';

describe('Tooltip', () => {
  it('renders trigger content and tooltip content', () => {
    render(<Tooltip content='Tooltip text'>Hover me</Tooltip>);

    expect(screen.getByText('Hover me')).toBeInTheDocument();
    expect(screen.getByRole('tooltip')).toHaveTextContent('Tooltip text');
  });

  it('merges an optional wrapper class name', () => {
    render(
      <Tooltip content='Tooltip text' className='custom-class'>
        Hover me
      </Tooltip>
    );

    expect(screen.getByText('Hover me').closest('span')).toHaveClass(
      'custom-class'
    );
  });
});
