import { useEffect, useRef } from "react";

interface EmbedRendererProps {
  html: string;
  className?: string;
}

/**
 * Renders third-party embed HTML and re-executes script tags
 * (dangerouslySetInnerHTML does not run scripts).
 * Only use for admin-controlled embed code.
 */
export function EmbedRenderer({ html, className }: EmbedRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !html) return;

    container.innerHTML = "";
    const wrapper = document.createElement("div");
    wrapper.innerHTML = html;

    Array.from(wrapper.querySelectorAll("script")).forEach((oldScript) => {
      const newScript = document.createElement("script");
      Array.from(oldScript.attributes).forEach((attr) =>
        newScript.setAttribute(attr.name, attr.value)
      );
      newScript.textContent = oldScript.textContent;
      oldScript.parentNode?.replaceChild(newScript, oldScript);
    });

    container.appendChild(wrapper);
  }, [html]);

  return (
    <div
      ref={containerRef}
      className={className ?? "pmw-embed-container min-h-[200px]"}
    />
  );
}
