import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import SceneCard from '../SceneCard'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { Scene } from '@/types'

vi.mock('@/lib/api', () => ({
  apiPost: vi.fn(),
  apiGet: vi.fn(),
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

// Mock components used by SceneCard that we don't need to test deeply here
vi.mock('../ShotList', () => ({
  __esModule: true,
  default: () => <div data-testid="shot-list" />
}))

vi.mock('../SceneAnalyses', () => ({
  __esModule: true,
  default: () => <div data-testid="scene-analyses" />
}))

const mockScene: Scene = {
  id: 1,
  project_id: 1,
  scene_number: 1,
  title: 'Test Scene',
  description: 'Test Description',
  location_type: 'interior',
  time_of_day: 'morning',
  mood: 'happy',
  notes: 'Test Notes',
  shots_count: 0,
}

describe('SceneCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders scene details properly', () => {
    render(<SceneCard scene={mockScene} />)
    expect(screen.getByText('Test Scene')).toBeInTheDocument()
    expect(screen.getByText('Scene 1')).toBeInTheDocument()
    expect(screen.getByText('Test Description')).toBeInTheDocument()
  })

  it('calls onEdit when edit button is clicked', () => {
    const onEdit = vi.fn()
    render(<SceneCard scene={mockScene} onEdit={onEdit} />)
    const editBtn = screen.getByTitle('Edit Scene')
    fireEvent.click(editBtn)
    expect(onEdit).toHaveBeenCalledWith(mockScene)
  })

  it('calls onDelete when delete button is clicked', () => {
    const onDelete = vi.fn()
    render(<SceneCard scene={mockScene} onDelete={onDelete} />)
    const deleteBtn = screen.getByTitle('Delete Scene')
    fireEvent.click(deleteBtn)
    expect(onDelete).toHaveBeenCalledWith(mockScene.id)
  })
})
