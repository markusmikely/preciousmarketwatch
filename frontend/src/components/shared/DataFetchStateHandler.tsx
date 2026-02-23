import { AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DataFetchStateHandlerProps {
  loading: boolean;
  error: Error | null;
  children: React.ReactNode;
  onRetry?: () => void;
  loadingMessage?: string;
}

/**
 * Reusable component for handling loading and error states
 * Shows loading spinner or error message, otherwise renders children
 */
export function DataFetchStateHandler({
  loading,
  error,
  children,
  onRetry,
  loadingMessage = "Loading content...",
}: DataFetchStateHandlerProps) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="h-8 w-8 text-primary animate-spin mb-4" />
        <p className="text-muted-foreground">{loadingMessage}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-6 my-6">
        <div className="flex items-start gap-4">
          <AlertCircle className="h-6 w-6 text-destructive flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-destructive mb-2">Error loading content</h3>
            <p className="text-sm text-destructive/80 mb-4">
              {error.message || 'An unexpected error occurred. Please try again.'}
            </p>
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="border-destructive/20 text-destructive hover:bg-destructive/5"
              >
                Try again
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
