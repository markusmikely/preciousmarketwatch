import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import { AlertCircle, Home, ArrowLeft } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { Button } from "@/components/ui/button";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <PageLayout>
      <div className="min-h-screen flex flex-col items-center justify-center px-4 py-24">
        <div className="max-w-md text-center">
          <div className="mb-6 flex justify-center">
            <AlertCircle className="h-20 w-20 text-destructive/60" />
          </div>
          
          <h1 className="font-display text-5xl font-bold text-foreground mb-2">404</h1>
          <h2 className="font-display text-2xl font-bold text-foreground mb-4">Page Not Found</h2>
          
          <p className="text-muted-foreground mb-8">
            The page you're looking for doesn't exist or may have moved. Don't worry, we have plenty of useful content to explore.
          </p>

          <div className="space-y-3 mb-12">
            <Button asChild className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
              <Link to="/">
                <Home className="h-4 w-4 mr-2" />
                Back to Home
              </Link>
            </Button>
            
            <Button asChild variant="outline" className="w-full">
              <Link to="/market-insights">
                <ArrowLeft className="h-4 w-4 mr-2" />
                View Market Insights
              </Link>
            </Button>
          </div>

          <div className="bg-muted/50 rounded-lg p-4 text-left">
            <p className="text-xs text-muted-foreground font-mono">
              Requested path: <code className="text-foreground">{location.pathname}</code>
            </p>
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

export default NotFound;
