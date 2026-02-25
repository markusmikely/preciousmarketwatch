import { useEffect, useState } from "react";
import { getWordPressRestBaseUrl } from "@/lib/wordPressRestUrl";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import type { PageSection } from "../PageBuilder";

interface Agent {
  id: string;
  name: string;
  role: string;
  tier: number;
  bio?: string;
  avatar?: string | null;
  specialisms?: string;
}

interface TeamGridSectionData {
  heading?: string | null;
  showTiers?: boolean | null;
  filterStatus?: string | null;
}

export function TeamGrid({ section }: { section: PageSection }) {
  const data = section as TeamGridSectionData;
  const [agents, setAgents] = useState<Agent[]>([]);
  const [byTier, setByTier] = useState<Agent[][]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const base = getWordPressRestBaseUrl();
    fetch(`${base}/pmw/v1/agents`)
      .then((r) => r.json())
      .then((d) => {
        setAgents(d.agents ?? []);
        setByTier(d.byTier ?? []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading && agents.length === 0) {
    return (
      <section className="py-16">
        <div className="container mx-auto px-4 lg:px-8">
          {data.heading && (
            <h2 className="font-display text-2xl font-bold text-foreground mb-8 text-center">
              {data.heading}
            </h2>
          )}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-card rounded-xl border border-border p-6 animate-pulse h-48" />
            ))}
          </div>
        </div>
      </section>
    );
  }

  const displayAgents = data.showTiers ? byTier.flat() : agents;
  if (displayAgents.length === 0) return null;

  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        {data.heading && (
          <h2 className="font-display text-2xl font-bold text-foreground mb-8 text-center">
            {data.heading}
          </h2>
        )}
        {data.showTiers && byTier.length > 0 ? (
          <div className="space-y-12">
            {byTier.map((tierAgents, tierIdx) => (
              <div key={tierIdx}>
                <h3 className="font-display text-lg font-semibold text-primary mb-4">
                  Tier {tierIdx + 1}
                </h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {tierAgents.map((agent) => (
                    <AgentCard key={agent.id} agent={agent} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {displayAgents.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function AgentCard({ agent }: { agent: Agent }) {
  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden">
      <div className="aspect-square overflow-hidden bg-muted">
        <Avatar className="w-full h-full rounded-none">
          <AvatarImage src={agent.avatar ?? undefined} alt={agent.name} />
          <AvatarFallback className="rounded-none text-2xl text-primary/70">
            {agent.name.charAt(0)}
          </AvatarFallback>
        </Avatar>
      </div>
      <div className="p-5">
        <h3 className="font-display text-lg font-semibold text-foreground">{agent.name}</h3>
        <span className="text-sm text-primary block mb-2">{agent.role}</span>
        {agent.bio && <p className="text-sm text-muted-foreground line-clamp-3">{agent.bio}</p>}
      </div>
    </div>
  );
}
