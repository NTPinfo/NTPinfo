import { render, screen, fireEvent } from '@testing-library/react';
import InputSection from '../../components/InputSection.tsx';
import {describe, vi, expect, test } from 'vitest'
import '@testing-library/jest-dom'


describe('InputSection', () => {
  const setup = (propsOverride = {}) => {
    const onClick = vi.fn();
    const onIPv6Toggle = vi.fn();

    const props = {
      onClick,
      ipv6Selected: false,
      onIPv6Toggle,
      measurementSessionActive: false,
      ...propsOverride,
    };

    render(<InputSection {...props} />);
    return { onClick, onIPv6Toggle };
  };

  test('Render Initial Input Field', () => {
    setup();
    expect(
      screen.getByText(/Enter the domain name or IP address/i)
    ).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/time\.google\.com/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /measure/i })).toBeInTheDocument();
  });

  test('Disable button when input is empty', () => {
    setup();

    const button = screen.getByRole('button', { name: /measure/i });

    expect(button).toBeDisabled();
    fireEvent.change(screen.getByPlaceholderText(/time\.google\.com/i), {
      target: { value: '   ' },
    });
    expect(button).toBeDisabled();
  });

  test('Triggers onClick on button click', () => {
    const { onClick } = setup({ ipv6Selected: true });

    const input = screen.getByPlaceholderText(/time\.google\.com/i);
    const button = screen.getByRole('button', { name: /measure/i });

    fireEvent.change(input, { target: { value: 'time.apple.com  ' } }); // spaces so trim is tested as well
    fireEvent.click(button);

    expect(onClick).toHaveBeenCalledWith('time.apple.com', true);
  });

  test('Trigger onClick on Enter', () => {
    const { onClick } = setup({ ipv6Selected: false });

    const input = screen.getByPlaceholderText(/time\.google\.com/i);

    fireEvent.change(input, { target: { value: 'example.com' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    expect(onClick).toHaveBeenCalledWith('example.com', false);
  });

  test('IPv6/IPv4 toggle', () => {
    const onIPv6Toggle = vi.fn()

    let ipv6Selected = false

     // triggers rerender to actually update the ipv6Selected variables
     const { rerender } = render(
      <InputSection
        onClick={() => {}}
        ipv6Selected={ipv6Selected}
        onIPv6Toggle={(val) => {
          onIPv6Toggle(val);
          ipv6Selected = val;  // update local state
          rerender(
            <InputSection
              onClick={() => {}}
              ipv6Selected={ipv6Selected}
              onIPv6Toggle={onIPv6Toggle}
              measurementSessionActive={false}
            />
          );
        }}
        measurementSessionActive={false}
      />
    );

    const ipv6Radio = screen.getByLabelText('IPv6');
    fireEvent.click(ipv6Radio);

    expect(onIPv6Toggle).toHaveBeenCalledWith(true);

    const ipv4Radio = screen.getByLabelText('IPv4');
    fireEvent.click(ipv4Radio);
    expect(onIPv6Toggle).toHaveBeenCalledWith(false);

  });

  test('Disable button while loading', () => {
    setup({ measurementSessionActive: true});

    const input = screen.getByPlaceholderText(/time\.google\.com/i);
    const button = screen.getByRole('button', { name: /measure/i });

    fireEvent.change(input, { target: { value: 'test' } });
    expect(button).toBeDisabled();
  });
});