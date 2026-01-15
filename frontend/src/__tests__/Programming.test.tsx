import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Programming from "../components/Programming";
import { ASSETS } from "../api/routes";

describe("Programming Component", () => {
  it("renders the under construction message", () => {
    render(<Programming />);
    expect(
      screen.getByText(/Oops, page is under construction/i),
    ).toBeInTheDocument();
  });

  it("applies the under construction background image correctly", () => {
    const { container } = render(<Programming />);
    // The container with background is the second div (index 1) or we can look for the class
    const backgroundDiv = container.querySelector('[class*="container"]');
    expect(backgroundDiv).toHaveStyle(
      `background-image: url(${ASSETS.underConstruction})`,
    );
  });
});
