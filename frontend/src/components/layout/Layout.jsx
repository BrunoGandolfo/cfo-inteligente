import PropTypes from 'prop-types';
import { ThemeProvider } from '../../context/ThemeContext';
import { FilterProvider } from '../../context/FilterContext';
import Header from './Header';
import Sidebar from './Sidebar';

export function Layout({ children }) {
  return (
    <ThemeProvider>
      <FilterProvider>
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950">
          <Header />
          <div className="pt-20 flex">
            <Sidebar />
            <main className="flex-1 p-6 overflow-y-auto">{children}</main>
          </div>
        </div>
      </FilterProvider>
    </ThemeProvider>
  );
}
Layout.propTypes = { children: PropTypes.node };
export default Layout;


