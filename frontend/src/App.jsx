import { BrowserRouter, Routes, Route } from "react-router-dom";
import Nav from "./components/Nav";
import Overview from "./pages/Overview";
import Investigations from "./pages/Investigations";
import NewInvestigation from "./pages/NewInvestigation";
import InvestigationDetail from "./pages/InvestigationDetail";

export default function App() {
  return (
    <BrowserRouter>
      <div className="layout">
        <Nav />
        <main className="main">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/investigations" element={<Investigations />} />
            <Route path="/investigations/new" element={<NewInvestigation />} />
            <Route path="/investigations/:id" element={<InvestigationDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}