import { NavLink } from "react-router-dom";

export default function Nav() {
  return (
    <nav className="nav">
      <div className="nav-brand">JOCKY</div>
      <div className="nav-links">
        <NavLink
          to="/"
          end
          className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
        >
          Overview
        </NavLink>
        <NavLink
          to="/investigations"
          className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
        >
          Investigations
        </NavLink>
        <NavLink
          to="/investigations/new"
          className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
        >
          New Investigation
        </NavLink>
      </div>
    </nav>
  );
}