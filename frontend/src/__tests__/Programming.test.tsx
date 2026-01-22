import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Programming from "../components/Programming";
import { Project } from "../types";
import { useAppStore } from "../store/useStore";

// Mock the store
jest.mock("../store/useStore");

describe("Programming Component", () => {
  const mockLoadProjects = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useAppStore as unknown as jest.Mock).mockReturnValue({
      projects: [],
      isProjectsLoading: false,
      error: null,
      loadProjects: mockLoadProjects,
    });
  });

  it("renders the Project Archive title", () => {
    render(<Programming />);
    expect(screen.getByText(/Project Archive/i)).toBeInTheDocument();
  });

  it("shows loading state correctly", () => {
    (useAppStore as unknown as jest.Mock).mockReturnValue({
      projects: [],
      isProjectsLoading: true,
      error: null,
      loadProjects: mockLoadProjects,
    });

    render(<Programming />);
    expect(screen.getByText(/Compiling projects/i)).toBeInTheDocument();
  });

  it("renders projects list", () => {
    const mockProjects: Project[] = [
      {
        pk: 1,
        name: "Test Project",
        description: "Test Description",
        technologies: "React, Node",
        technologies_list: ["React", "Node"],
        github_url: "http://github.com",
        live_url: "http://live.com",
        images: [{ pk: 1, url: "test.jpg", name: "Test", is_cover: true }],
        created_at: "2023-01-01",
        updated_at: "2023-01-01",
      },
    ];

    (useAppStore as unknown as jest.Mock).mockReturnValue({
      projects: mockProjects,
      isProjectsLoading: false,
      error: null,
      loadProjects: mockLoadProjects,
    });

    render(<Programming />);
    expect(screen.getByText("Test Project")).toBeInTheDocument();
    expect(screen.getByText("Test Description")).toBeInTheDocument();
  });
});
