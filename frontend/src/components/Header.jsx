import { Button } from '@/components/ui/button';
import { logout } from '../api';
import { Link } from 'react-router-dom';

const Header = ({ setIsAuthenticated }) => {
  const handleLogout = () => {
    logout();
    setIsAuthenticated(false);
  };

  return (
    <header className="bg-primary text-primary-foreground p-4">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-2xl font-bold">Financial Document Analyzer</h1>
        <nav className="space-x-4">
          <Link to="/"><Button variant="ghost">Dashboard</Button></Link>
          <Link to="/history"><Button variant="ghost">History</Button></Link>
          <Button onClick={handleLogout} variant="outline">Logout</Button>
        </nav>
      </div>
    </header>
  );
};

export default Header;