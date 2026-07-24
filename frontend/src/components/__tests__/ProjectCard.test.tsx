import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import ProjectCard from '../ProjectCard'
import { useRouter } from 'next/navigation'
import { vi, describe, it, expect } from 'vitest'
import { Project } from '@/types'

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}))

const mockProject: Project = {
  id: 1,
  title: 'Test Project',
  description: 'Project Description',
  status: 'draft',
  genre: 'action',
  scenes_count: 5,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
}

describe('ProjectCard', () => {
  it('renders project details properly', () => {
    ;(useRouter as any).mockReturnValue({ push: vi.fn() })
    render(<ProjectCard project={mockProject} />)
    expect(screen.getByText('Test Project')).toBeInTheDocument()
    expect(screen.getByText('Project Description')).toBeInTheDocument()
    expect(screen.getByText('Draft')).toBeInTheDocument()
    expect(screen.getByText('action')).toBeInTheDocument()
    expect(screen.getByText(/5 scenes/)).toBeInTheDocument()
  })

  it('navigates to project on click', () => {
    const pushMock = vi.fn()
    ;(useRouter as any).mockReturnValue({ push: pushMock })
    render(<ProjectCard project={mockProject} />)
    const card = screen.getByRole('link')
    fireEvent.click(card)
    expect(pushMock).toHaveBeenCalledWith(`/project/${mockProject.id}`)
  })
})
