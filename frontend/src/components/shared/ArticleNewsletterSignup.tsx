import { useState } from "react";
import { Mail, Loader2, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { subscribeNewsletter } from "@/services/newsletter";

export function ArticleNewsletterSignup() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setStatus("loading");
    setMessage("");

    const result = await subscribeNewsletter(email.trim(), ["article-signup"]);

    if (result.success) {
      setStatus("success");
      setEmail("");
    } else {
      setStatus("error");
      setMessage(result.message || "Something went wrong. Please try again.");
    }
  };

  if (status === "success") {
    return (
      <div className="bg-gradient-hero rounded-xl p-6">
        <div className="flex items-center gap-3 text-silver-light">
          <CheckCircle className="h-6 w-6 shrink-0 text-primary" />
          <p className="font-medium">You're subscribed!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-hero rounded-xl p-6">
      <h3 className="font-display text-lg font-bold text-silver-light mb-2">
        Stay Updated
      </h3>
      <p className="text-sm text-silver mb-4">
        Get weekly market insights delivered to your inbox.
      </p>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <Input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={status === "loading"}
            required
            aria-invalid={status === "error"}
            className={`w-full bg-navy border-silver/30 text-silver-light placeholder:text-silver/60 focus:outline-none focus:border-primary ${
              status === "error" ? "border-destructive" : ""
            }`}
          />
          {status === "error" && message && (
            <p role="alert" className="mt-1 text-sm text-destructive">
              {message}
            </p>
          )}
        </div>
        <Button
          type="submit"
          disabled={status === "loading"}
          className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
        >
          {status === "loading" ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Subscribing…
            </>
            ) : (
              <>
                <Mail className="mr-2 h-4 w-4" />
                Subscribe
              </>
            )}
        </Button>
      </form>
    </div>
  );
}
