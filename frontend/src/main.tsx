import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import { AppQueryProvider } from "./app/providers/AppQueryProvider";
import "./app/styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppQueryProvider>
      <App />
    </AppQueryProvider>
  </React.StrictMode>
);
