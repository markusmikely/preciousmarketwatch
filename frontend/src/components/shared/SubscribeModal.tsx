import { useState } from "react";
import { Mail, X, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { subscribeNewsletter } from "@/services/newsletter";

interface SubscribeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SubscribeModal({ open, onOpenChange }: SubscribeModalProps) {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setError(null);
    setIsSubmitting(true);

    const result = await subscribeNewsletter(email);

    setIsSubmitting(false);
    if (result.success) {
      setIsSuccess(true);
      setEmail("");
      setTimeout(() => {
        onOpenChange(false);
        setIsSuccess(false);
      }, 2000);
    } else {
      setError(result.message);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        {isSuccess ? (
          <div className="flex flex-col items-center py-8 text-center">
            <div className="mb-4 rounded-full bg-success/10 p-3">
              <CheckCircle className="h-8 w-8 text-success" />
            </div>
            <h3 className="font-display text-xl font-bold text-foreground">
              You're subscribed!
            </h3>
            <p className="mt-2 text-muted-foreground">
              Check your inbox for a confirmation email.
            </p>
          </div>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="font-display text-xl">
                Subscribe to Market Insights
              </DialogTitle>
              <DialogDescription>
                Get weekly analysis on precious metals, gemstones, and investment
                opportunities delivered to your inbox.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="mt-4 space-y-4">
              <div className="space-y-2">
                <Input
                  type="email"
                  placeholder="Enter your email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full"
                  aria-invalid={!!error}
                />
                {error && (
                  <p role="alert" className="text-sm text-destructive">
                    {error}
                  </p>
                )}
              </div>
              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
              >
                {isSubmitting ? (
                  "Subscribing..."
                ) : (
                  <>
                    <Mail className="mr-2 h-4 w-4" />
                    Subscribe
                  </>
                )}
              </Button>
              <p className="text-center text-xs text-muted-foreground">
                No spam. Unsubscribe anytime. We respect your privacy.
              </p>
            </form>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
