import { createBrowserRouter } from "react-router";
import { RootProvider } from "./components/RootProvider";
import { Layout } from "./components/Layout";
import { MachineSelection } from "./components/MachineSelection";
import { CameraScreen } from "./components/CameraScreen";
import { MaintenanceHistory } from "./components/MaintenanceHistory";
import { Analytics } from "./components/Analytics";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootProvider,
    children: [
      {
        Component: Layout,
        children: [
          { index: true, Component: MachineSelection },
          { path: "history", Component: MaintenanceHistory },
          { path: "analytics", Component: Analytics },
        ],
      },
      {
        path: "camera/:machineId",
        Component: CameraScreen,
      },
    ],
  },
]);
