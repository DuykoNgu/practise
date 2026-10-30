import { useQuery } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { Providers } from "@/app/providers";

function Greeting() {
  const { data } = useQuery({
    queryKey: ["greeting"],
    queryFn: () => Promise.resolve("ready"),
  });
  return <p>{data}</p>;
}

test("provides a query client to client components", async () => {
  render(
    <Providers>
      <Greeting />
    </Providers>,
  );
  expect(await screen.findByText("ready")).toBeInTheDocument();
});
