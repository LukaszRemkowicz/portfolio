import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import HomePage from "../HomePage";
import { UserProfile } from "../types";
import { fetchProfile } from "../api/services";

// Mock the API services
jest.mock("../api/services", () => ({
  fetchProfile: jest.fn(),
  fetchBackground: jest.fn().mockResolvedValue("/test-bg.jpg"),
  fetchEnabledFeatures: jest.fn().mockResolvedValue({}),
}));

describe("HomePage Component", () => {
  const mockFetchProfile = fetchProfile as jest.MockedFunction<
    typeof fetchProfile
  >;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("shows loading state initially", async () => {
    mockFetchProfile.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                first_name: "John",
                last_name: "Doe",
                short_description: "Professional Photographer",
                avatar: null,
                bio: "Test bio",
                about_me_image: null,
                about_me_image2: null,
              }),
            100,
          ),
        ),
    );

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>,
    );

    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders profile data after loading", async () => {
    const mockProfile: UserProfile = {
      first_name: "John",
      last_name: "Doe",
      short_description: "Professional Photographer",
      avatar: "/test-avatar.jpg",
      bio: "This is a test bio",
      about_me_image: null,
      about_me_image2: null,
    };

    mockFetchProfile.mockResolvedValue(mockProfile);

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("The Beauty of")).toBeInTheDocument();
    });

    expect(screen.getByText("This is a test bio")).toBeInTheDocument();
  });
});
