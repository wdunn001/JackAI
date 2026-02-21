import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { Chat } from "./pages/Chat";
import { Scanner } from "./pages/Scanner";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/scan" element={<Scanner />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
