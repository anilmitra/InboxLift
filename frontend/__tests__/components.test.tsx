import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

describe("Button component", () => {
  it("renders with text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("shows loading spinner when loading=true", () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByText("Loading")).toBeInTheDocument();
    // Button should be disabled when loading
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("calls onClick when clicked", () => {
    const onClick = jest.fn();
    render(<Button onClick={onClick}>Click</Button>);
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("does not call onClick when disabled", () => {
    const onClick = jest.fn();
    render(<Button onClick={onClick} disabled>Click</Button>);
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).not.toHaveBeenCalled();
  });

  it("applies variant classes", () => {
    const { rerender } = render(<Button variant="outline">Outline</Button>);
    expect(screen.getByRole("button")).toHaveClass("border");

    rerender(<Button variant="destructive">Delete</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-destructive");
  });
});

describe("Badge component", () => {
  it("renders with text", () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("applies variant styles", () => {
    const { container } = render(<Badge variant="success">OK</Badge>);
    expect(container.firstChild).toHaveClass("bg-green-100");
  });

  it("applies error variant", () => {
    const { container } = render(<Badge variant="error">Error</Badge>);
    expect(container.firstChild).toHaveClass("bg-red-100");
  });
});

describe("Card component", () => {
  it("renders children", () => {
    render(
      <Card>
        <CardContent>Card body</CardContent>
      </Card>
    );
    expect(screen.getByText("Card body")).toBeInTheDocument();
  });

  it("renders title", () => {
    render(<CardTitle>My Card</CardTitle>);
    expect(screen.getByText("My Card")).toBeInTheDocument();
  });
});

describe("Input component", () => {
  it("renders with label", () => {
    render(<Input label="Email" />);
    expect(screen.getByText("Email")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("shows error message", () => {
    render(<Input label="Email" error="Invalid email" />);
    expect(screen.getByText("Invalid email")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toHaveClass("border-destructive");
  });

  it("shows hint message", () => {
    render(<Input label="Password" hint="At least 8 characters" />);
    expect(screen.getByText("At least 8 characters")).toBeInTheDocument();
  });

  it("handles user input", () => {
    render(<Input label="Name" />);
    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "John" } });
    expect(input).toHaveValue("John");
  });
});
