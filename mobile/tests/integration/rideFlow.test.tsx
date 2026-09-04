/**
 * T047: mobile integration test — happy-path PostIntent → matched → navigate to MatchReview.
 *
 * Mocks the network layer (apiClient) only; exercises the real PostIntentScreen component,
 * the real useIntentStatus polling hook, and the real navigation.navigate call.
 */
import React from 'react';
import { act, fireEvent, render, waitFor } from '@testing-library/react-native';

import PostIntentScreen from '../../src/screens/PostIntent';
import * as apiClient from '../../src/services/apiClient';

jest.mock('../../src/services/apiClient');

const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

function buildNavigationProps() {
  const navigate = jest.fn();
  return {
    navigation: { navigate } as any,
    route: { key: 'PostIntent', name: 'PostIntent' } as any,
  };
}

describe('PostIntent → matched flow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('submits the intent, polls until matched, and navigates to MatchReview with the match id', async () => {
    mockedApiClient.createRideIntent.mockResolvedValue({
      id: 'intent-1',
      status: 'open',
    } as apiClient.RideIntent);
    mockedApiClient.getRideIntent.mockResolvedValue({
      id: 'intent-1',
      status: 'matched',
      match_id: 'match-1',
    } as apiClient.RideIntent);

    const props = buildNavigationProps();
    const { getByPlaceholderText, getByText } = render(<PostIntentScreen {...props} />);

    fireEvent.changeText(getByPlaceholderText('Pune Jn'), 'Pune Junction');
    fireEvent.changeText(getByPlaceholderText('Baner'), 'Baner');
    fireEvent.changeText(getByPlaceholderText('YYYY-MM-DDTHH:mm'), '2030-01-01T09:00');

    await act(async () => {
      fireEvent.press(getByText('Find a ride share'));
    });

    expect(mockedApiClient.createRideIntent).toHaveBeenCalledWith(
      expect.objectContaining({
        origin_station: 'Pune Junction',
        destination: 'Baner',
        luggage_size: 'small',
        gender_preference: 'any',
      })
    );

    await waitFor(() => {
      expect(props.navigation.navigate).toHaveBeenCalledWith('MatchReview', { matchId: 'match-1' });
    });
  });
});
