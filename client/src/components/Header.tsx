import '../styles/Header.css'
import github from '../assets/github-svgrepo-com.png'
import NTPinfoLogo from '../assets/NTPinfo.png'

function Header() {
    return (
        <div className="header">
            <div className="text-header">
                <img src={NTPinfoLogo} alt="NTPinfo Logo" className="ntpinfo-logo"/>
                <h1 id="title">NTPinfo</h1>
                {/* <p>A tool to evaluate the accuracy of publicly available NTP servers</p> */}
            </div>
            <nav className="navbar">
                {/* <a href="#" aria-label="About">About</a> */}
                <div className="img-and-text">
                    <a href="https://github.com/NTPinfo/NTPinfo" target="_blank" rel="noopener noreferrer"
                       aria-label="GitHub Repository">Github</a>
                    <a href="https://github.com/NTPinfo/NTPinfo" target="_blank" rel="noopener noreferrer"
                       aria-label="GitHub Repository">
                        <img src={github} alt="GitHub Logo"/>
                    </a>
                </div>
            </nav>
        </div>
    );
}

export default Header