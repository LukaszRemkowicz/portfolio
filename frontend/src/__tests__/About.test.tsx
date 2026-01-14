import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import About from "../About";
import { UserProfile } from "../types";

describe("About Component", () => {
  it("renders nothing when profile is null", () => {
    const { container } = render(<About profile={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders profile bio from props", () => {
    const mockProfile: UserProfile = {
      first_name: "John",
      last_name: "Doe",
      short_description: "Test Short Description",
      avatar: null,
      bio: "This is a test bio with multiple lines.\nIt should display correctly.",
      about_me_image: null,
      about_me_image2: null,
    };

    render(<About profile={mockProfile} />);

    expect(screen.getByText("About me")).toBeInTheDocument();
    expect(
      screen.getByText(/This is a test bio with multiple lines/),
    ).toBeInTheDocument();
  });

  it("renders about me image when available in props", () => {
    const mockProfile: UserProfile = {
      first_name: "John",
      last_name: "Doe",
      short_description: "Test Short Description",
      avatar: null,
      bio: "Test bio",
      about_me_image: "/test-image.jpg",
      about_me_image2: null,
    };

    render(<About profile={mockProfile} />);

    expect(screen.getByText("About me")).toBeInTheDocument();
    const image = screen.getByAltText("About me");
    expect(image).toHaveAttribute("src", "/test-image.jpg");
  });
});
