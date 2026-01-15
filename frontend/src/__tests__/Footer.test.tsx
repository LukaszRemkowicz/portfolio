import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Footer from "../Footer";

describe("Footer Component", () => {
  it("renders copyright text", () => {
    render(<Footer />);
    expect(screen.getByText("Celestial © 2024")).toBeInTheDocument();
  });

  it("renders social links", () => {
    render(<Footer />);
    expect(screen.getByText("Instagram")).toBeInTheDocument();
    expect(screen.getByText("Astrobin")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
  });
});
