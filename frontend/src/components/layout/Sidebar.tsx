import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ListTodo, Settings, Database, Upload } from 'lucide-react';

const navigation = [
  { name: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { name: 'Tasks', to: '/tasks', icon: ListTodo },
  { name: 'Import', to: '/import', icon: Upload },
  { name: 'Content', to: '/content', icon: Database },
  { name: 'Settings', to: '/settings', icon: Settings },
];

export const Sidebar = () => {
  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col h-screen">
      <div className="p-6">
        <div className="flex items-center gap-2">
          <Database className="h-8 w-8 text-blue-400" />
          <span className="text-lg font-bold">KB Manager</span>
        </div>
      </div>

      <nav className="px-3 mt-6 flex-1">
        <ul className="space-y-1">
          {navigation.map((item) => (
            <li key={item.name}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`
                }
              >
                <item.icon className="h-5 w-5" />
                <span className="font-medium">{item.name}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-4 border-t border-gray-800 mt-auto">
        <div className="text-xs text-gray-400 text-center">
          <p>Version 1.0.0</p>
          <p className="mt-1">Production Ready</p>
        </div>
      </div>
    </aside>
  );
};
