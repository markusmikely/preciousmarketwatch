import { useState } from "react";
import { Mail, Building, Newspaper, Send, Loader2 } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { submitContactForm } from "@/services/contact";

const inquiryTypes = [
  { id: "general", label: "General Inquiry", icon: Mail },
  { id: "partnership", label: "Partnership", icon: Building },
  { id: "press", label: "Press & Media", icon: Newspaper },
];

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

export default function Contact() {
  const [selectedType, setSelectedType] = useState("general");
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    subject: "",
    message: "",
  });
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [submitError, setSubmitError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Client-side validation
    const err: Record<string, string> = {};
    if (!formData.name.trim()) err.name = "Name is required.";
    if (!formData.email.trim()) err.email = "Email is required.";
    else if (!isValidEmail(formData.email)) err.email = "Please enter a valid email address.";
    if (!formData.subject.trim()) err.subject = "Subject is required.";
    if (!formData.message.trim()) err.message = "Message is required.";
    setFieldErrors(err);
    if (Object.keys(err).length > 0) return;

    setStatus("loading");
    setSubmitError("");

    const result = await submitContactForm({
      name: formData.name,
      email: formData.email,
      subject: formData.subject,
      message: formData.company.trim()
        ? `Company: ${formData.company}\n\n${formData.message}`
        : formData.message,
    });

    setStatus(result.success ? "success" : "error");
    if (result.success) {
      setFormData({ name: "", email: "", company: "", subject: "", message: "" });
      setFieldErrors({});
    } else {
      setSubmitError(result.message);
      if (result.errors) setFieldErrors(result.errors);
    }
  };

  return (
    <PageLayout showTicker={false}>
      <PageHero
        title="Contact Us"
        subtitle="Have questions, partnership inquiries, or press requests? We'd love to hear from you."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Contact" },
        ]}
      />

      <section className="py-16">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="grid lg:grid-cols-3 gap-12">
            {/* Contact Info */}
            <div className="lg:col-span-1">
              <h2 className="font-display text-xl font-bold text-foreground mb-6">Get in Touch</h2>
              
              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold text-foreground mb-2">Email</h3>
                  <p className="text-muted-foreground">contact@preciousmarketwatch.com</p>
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-2">Press Inquiries</h3>
                  <p className="text-muted-foreground">press@preciousmarketwatch.com</p>
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-2">Partnerships</h3>
                  <p className="text-muted-foreground">partners@preciousmarketwatch.com</p>
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-2">Response Time</h3>
                  <p className="text-muted-foreground">We typically respond within 24-48 business hours.</p>
                </div>
              </div>

              <div className="mt-8 p-6 bg-muted/50 rounded-xl">
                <h3 className="font-semibold text-foreground mb-2">Advertise With Us</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Reach 500K+ monthly readers interested in precious metals and gemstones.
                </p>
                <Button variant="outline" size="sm">
                  Download Media Kit
                </Button>
              </div>
            </div>

            {/* Contact Form */}
            <div className="lg:col-span-2">
              <div className="bg-card rounded-xl border border-border p-8">
                {status === "success" ? (
                  <div className="py-8 text-center">
                    <p className="text-lg font-medium text-foreground">
                      Your message has been sent. We'll be in touch shortly.
                    </p>
                  </div>
                ) : (
                  <>
                    <h2 className="font-display text-xl font-bold text-foreground mb-6">Send a Message</h2>

                    {/* Inquiry Type Selection */}
                    <div className="flex flex-wrap gap-3 mb-8">
                      {inquiryTypes.map((type) => (
                        <button
                          key={type.id}
                          type="button"
                          onClick={() => setSelectedType(type.id)}
                          className={`flex items-center gap-2 px-4 py-2 rounded-full border transition-all ${
                            selectedType === type.id
                              ? "bg-primary text-primary-foreground border-primary"
                              : "bg-background border-border text-muted-foreground hover:border-primary hover:text-foreground"
                          }`}
                        >
                          <type.icon className="h-4 w-4" />
                          {type.label}
                        </button>
                      ))}
                    </div>

                    {submitError && (
                      <p role="alert" className="mb-4 text-sm text-destructive">
                        {submitError}
                      </p>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                      <div className="grid md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label htmlFor="name">Full Name *</Label>
                          <Input
                            id="name"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            required
                            disabled={status === "loading"}
                            placeholder="John Smith"
                            className={fieldErrors.name ? "border-destructive" : ""}
                          />
                          {fieldErrors.name && (
                            <p className="text-sm text-destructive">{fieldErrors.name}</p>
                          )}
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="email">Email Address *</Label>
                          <Input
                            id="email"
                            type="email"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            required
                            disabled={status === "loading"}
                            placeholder="john@example.com"
                            className={fieldErrors.email ? "border-destructive" : ""}
                          />
                          {fieldErrors.email && (
                            <p className="text-sm text-destructive">{fieldErrors.email}</p>
                          )}
                        </div>
                      </div>

                      <div className="grid md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label htmlFor="company">Company {selectedType !== "general" && "*"}</Label>
                          <Input
                            id="company"
                            value={formData.company}
                            onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                            required={selectedType !== "general"}
                            disabled={status === "loading"}
                            placeholder="Company Name"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="subject">Subject *</Label>
                          <Input
                            id="subject"
                            value={formData.subject}
                            onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                            required
                            disabled={status === "loading"}
                            placeholder="How can we help?"
                            className={fieldErrors.subject ? "border-destructive" : ""}
                          />
                          {fieldErrors.subject && (
                            <p className="text-sm text-destructive">{fieldErrors.subject}</p>
                          )}
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="message">Message *</Label>
                        <Textarea
                          id="message"
                          value={formData.message}
                          onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                          required
                          disabled={status === "loading"}
                          placeholder="Tell us more about your inquiry..."
                          rows={6}
                          className={fieldErrors.message ? "border-destructive" : ""}
                        />
                        {fieldErrors.message && (
                          <p className="text-sm text-destructive">{fieldErrors.message}</p>
                        )}
                      </div>

                      <Button
                        type="submit"
                        size="lg"
                        disabled={status === "loading"}
                        className="w-full md:w-auto bg-primary text-primary-foreground hover:bg-primary/90"
                      >
                        {status === "loading" ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Sending…
                          </>
                        ) : (
                          <>
                            <Send className="mr-2 h-4 w-4" />
                            Send Message
                          </>
                        )}
                      </Button>
                    </form>
                  </>
                )}
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
