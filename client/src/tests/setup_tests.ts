import { server } from '../mocks/server'
import { beforeAll, afterAll, afterEach, vi } from 'vitest'

/**
 * File to setup the mock server for the tests to call
 */

// Set up environment variables for tests
beforeAll(() => {
    // Set default VITE_STATUS_THRESHOLD for tests if not already set
    if (!import.meta.env.VITE_STATUS_THRESHOLD) {
        vi.stubEnv('VITE_STATUS_THRESHOLD', '1000')
    }
    server.listen()
})
afterEach(() => server.resetHandlers())
afterAll(() => server.close())