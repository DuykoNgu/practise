import { formatDateTime } from "@/lib/format";

test("converts UTC to the viewer time zone and shows the zone", () => {
  const formatted = formatDateTime("2026-10-30T01:15:00Z", "Asia/Ho_Chi_Minh");
  expect(formatted).toContain("08:15");
  expect(formatted).toMatch(/GMT\+7|UTC\+7/);
});

test("the same instant differs across zones", () => {
  expect(formatDateTime("2026-10-30T01:15:00Z", "UTC")).toContain("01:15");
});

test("shows a dash for an invalid date", () => {
  expect(formatDateTime("nonsense", "UTC")).toBe("—");
});
