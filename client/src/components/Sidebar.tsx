import React from 'react';
import '../styles/Sidebar.css';
import houseIcon from '../assets/house-svgrepo-com.png';
import compareIcon from '../assets/scale-unbalanced-svgrepo-com.png';
import graphIcon from '../assets/graph-svgrepo-com.png';
import aboutIcon from '../assets/info-square-svgrepo-com.png';
import SearchIcon from './SearchIcon';
import hamburgerIcon from '../assets/hamburger-md-svgrepo-com.png';

interface SidebarProps {
  selectedTab: number;
  setSelectedTab: (tab: number) => void;
  open: boolean;
  setOpen: (open: boolean) => void;
  isMeasurementRunning: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ selectedTab, setSelectedTab, open, setOpen, isMeasurementRunning }) => {
  const navItems = [
    {
      id: 1,
      label: 'Home',
      icon: <img src={houseIcon} alt="Home" className="sidebar__icon" />,
    },
    {
      id: 2,
      label: 'Historical Data',
      icon: <img src={graphIcon} alt="Graph" className="sidebar__icon" />,
    },
    {
      id: 3,
      label: 'Compare',
      icon: <img src={compareIcon} alt="Compare" className="sidebar__icon" />,
    },
    // SearchTab temporarily hidden - will be updated in future
    // {
    //   id: 4,
    //   label: 'Search',
    //   icon: <SearchIcon className="sidebar__icon" />,
    // },
    {
      id: 5,
      label: 'About',
      icon: <img src={aboutIcon} alt="About" className="sidebar__icon" />,
    },
  ];

  const handleTabClick = (tabId: number) => {
    if (isMeasurementRunning) {
      return; // Prevent tab switching when measurement is running
    }
    setSelectedTab(tabId);
  };

  return (
    <>
      {open && <div className="sidebar__overlay" onClick={() => setOpen(false)} />}
      <aside className={`sidebar ${open ? 'open' : 'closed'}`}>
        <button
          className="sidebar__toggle"
          onClick={() => setOpen(!open)}
          aria-label="Toggle sidebar"
        >
          <img src={hamburgerIcon} alt="Menu" className="sidebar__icon" />
        </button>

        {isMeasurementRunning && open && (
          <div className="sidebar__measurement-notice">
            <span>Measurement session in progress...</span>
          </div>
        )}

        <nav className="sidebar__nav">
          {navItems.map(({ id, label, icon }) => (
            <button
              key={id}
              className={`sidebar__item ${selectedTab === id ? 'active' : ''} ${isMeasurementRunning && selectedTab !== id ? 'disabled' : ''}`}
              onClick={() => handleTabClick(id)}
              aria-current={selectedTab === id ? 'page' : undefined}
              disabled={isMeasurementRunning && selectedTab !== id}
              title={isMeasurementRunning && selectedTab !== id ? 'Please wait for measurement session to complete' : undefined}
            >
              {icon}
              {open && <span className="sidebar__label">{label}</span>}
            </button>
          ))}
        </nav>
      </aside>
    </>
  );
};

export default Sidebar