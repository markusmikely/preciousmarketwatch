interface ReactToolPlaceholderProps {
  tool: {
    title?: string | null;
    excerpt?: string | null;
  };
}

export function ReactToolPlaceholder({ tool }: ReactToolPlaceholderProps) {
  return (
    <div className="rounded-xl border border-border bg-muted/30 p-8 text-center">
      <span className="inline-block rounded-full bg-primary/20 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-primary">
        Coming soon
      </span>
      <h2 className="font-display text-xl font-semibold text-foreground mt-4">
        {tool.title ?? "Tool"}
      </h2>
      {tool.excerpt && (
        <p className="mt-2 text-sm text-muted-foreground max-w-lg mx-auto">
          {tool.excerpt}
        </p>
      )}
    </div>
  );
}
