import { Outlet } from "react-router";
import { InspectionProvider } from "../context/InspectionContext";

export function RootProvider() {
  return (
    <InspectionProvider>
      <Outlet />
    </InspectionProvider>
  );
}
