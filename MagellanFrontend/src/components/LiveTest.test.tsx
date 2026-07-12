import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, test, expect, vi } from 'vitest'
import { LiveTest } from './LiveTest'
import { api } from '../api'

vi.mock('../api', () => ({
  api: {
    getHealth: vi.fn(() => Promise.resolve({ status: 'ok' })),
    triggerWorkflow: vi.fn(() => Promise.resolve({ workflow_id: 'test-workflow-1' })),
  },
}))

describe('LiveTest component', () => {
  test('loads default preset and can trigger workflow', async () => {
    render(<LiveTest />)

    // Should show the top header
    expect(screen.getByText(/Autonomous Diagnostic Engine/i)).toBeInTheDocument()

    // Wait for textarea to be populated with JSON
    await waitFor(() => expect(screen.getByRole('textbox')).not.toHaveValue(''))

    // Click submit button
    const button = screen.getByRole('button', { name: /Fire Sandbox Signal/i })
    fireEvent.click(button)

    // Expect the mocked API to have been called
    await waitFor(() => expect((api as any).triggerWorkflow).toHaveBeenCalled())

    // Expect initial terminal log to appear quickly (addLog with 0ms)
    await waitFor(() => expect(screen.getByText(/Initializing search-ops operator trigger context/i)).toBeInTheDocument())
  })
})
