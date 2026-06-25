import React from "react";
import { NavLink } from "react-router-dom";
import { 
  FiGrid, 
  FiCamera, 
  FiList, 
  FiFileText, 
  FiInfo, 
  FiSettings 
} from "react-icons/fi";

interface SidebarItem {
  name: string;
  path: string;
  icon: React.ReactNode;
}

export const Sidebar: React.FC = () => {
  const menuItems: SidebarItem[] = [
    {
      name: "Dashboard",
      path: "/",
      icon: <FiGrid className="text-lg" />,
    },
    {
      name: "Track Inspection",
      path: "/inspection",
      icon: <FiCamera className="text-lg" />,
    },
    {
      name: "Inference History",
      path: "/history",
      icon: <FiList className="text-lg" />,
    },
    {
      name: "Inspection Reports",
      path: "/reports",
      icon: <FiFileText className="text-lg" />,
    },
    {
      name: "Model Specs",
      path: "/model",
      icon: <FiInfo className="text-lg" />,
    },
    {
      name: "System Settings",
      path: "/settings",
      icon: <FiSettings className="text-lg" />,
    },
  ];

  return (
    <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col justify-between shrink-0 h-[calc(100vh-64px)] sticky top-16">
      {/* Sidebar Navigation Items */}
      <div className="py-6 px-4 space-y-1.5 flex-1">
        <span className="text-[10px] uppercase font-bold text-gray-500 tracking-widest px-3 block mb-4">
          Control Center Modules
        </span>
        
        {menuItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            // Strict match for home page to avoid highlighting Dashboard on all subpages
            end={item.path === "/"}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-3 py-3 rounded-lg text-sm font-medium tracking-wide transition-all duration-150 ${
                isActive
                  ? "bg-accent-blue/10 text-accent-blue border-l-4 border-accent-blue shadow-inner"
                  : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
              }`
            }
          >
            {item.icon}
            <span>{item.name}</span>
          </NavLink>
        ))}
      </div>

      {/* Sidebar Footer details */}
      <div className="p-4 border-t border-gray-800 bg-gray-950/20 text-center">
        <p className="text-[10px] text-gray-500 font-semibold tracking-wider">
          Indian Railways AI Core
        </p>
        <p className="text-[8px] text-gray-600 mt-0.5 uppercase tracking-widest">
          Classified Operations
        </p>
      </div>
    </aside>
  );
};
export default Sidebar;
