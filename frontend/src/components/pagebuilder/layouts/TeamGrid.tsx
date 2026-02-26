import { useEffect, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { AgentProfileModal } from "../AgentProfileModal";
import { fetchAgents, type Agent } from "@/services/agents";
import type { PageSection } from "../PageBuilder";

interface TeamGridSectionData {
  heading?: string | null;
  showTiers?: boolean | null;
  filterStatus?: string | null;
}

const TIER_ORDER = ["intelligence", "editorial", "production"];
const TIER_LABELS: Record<string, string> = {
  intelligence: "Intelligence",
  editorial: "Editorial",
  production: "Production",
};

export function TeamGrid({ section }: { section: PageSection }) {
  const data = section as TeamGridSectionData;
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    fetchAgents("all")
      .then(setAgents)
      .catch(() => setAgents([]))
      .finally(() => setLoading(false));
  }, []);

  const byTier: { tier: string; agents: Agent[] }[] = data.showTiers
    ? TIER_ORDER.map((tier) => ({
        tier,
        agents: agents
          .filter((a) => a.tier === tier)
          .sort((a, b) => a.display_order - b.display_order),
      })).filter((g) => g.agents.length > 0)
    : [];

  const displayAgents = data.showTiers ? byTier.flatMap((g) => g.agents) : agents;

  const handleAgentClick = (agent: Agent) => {
    setSelectedAgent(agent);
    setModalOpen(true);
  };

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
              <div
                key={i}
                className="bg-card rounded-xl border border-border p-6 animate-pulse h-48"
              />
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (displayAgents.length === 0) return null;

  return (
    <>
      <section className="py-16">
        <div className="container mx-auto px-4 lg:px-8">
          {data.heading && (
            <h2 className="font-display text-2xl font-bold text-foreground mb-8 text-center">
              {data.heading}
            </h2>
          )}
          {data.showTiers && byTier.length > 0 ? (
            <div className="space-y-12">
              {byTier.map((group) => (
                <div key={group.tier}>
                  <h3 className="font-display text-lg font-semibold text-primary mb-4">
                    {TIER_LABELS[group.tier] ?? group.tier}
                  </h3>
                  <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {group.agents.map((agent) => (
                      <AgentCard
                        key={agent.id}
                        agent={agent}
                        onClick={() => handleAgentClick(agent)}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {displayAgents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  onClick={() => handleAgentClick(agent)}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      <AgentProfileModal
        agent={selectedAgent}
        open={modalOpen}
        onOpenChange={setModalOpen}
      />
    </>
  );
}

function AgentCard({
  agent,
  onClick,
}: {
  agent: Agent;
  onClick: () => void;
}) {
  const avatarUrl =
    agent.avatar_image_url ?? agent.avatar_video_url ?? null;

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left bg-card rounded-xl border border-border overflow-hidden hover:border-primary/50 hover:shadow-md transition-all focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
    >
      <div className="aspect-square overflow-hidden bg-muted">
        <Avatar className="w-full h-full rounded-none">
          <AvatarImage src={avatarUrl ?? undefined} alt={agent.display_name} />
          <AvatarFallback className="rounded-none text-2xl text-primary/70">
            {agent.display_name.charAt(0)}
          </AvatarFallback>
        </Avatar>
      </div>
      <div className="p-5">
        <h3 className="font-display text-lg font-semibold text-foreground">
          {agent.display_name}
        </h3>
        <span className="text-sm text-primary block mb-2">{agent.role}</span>
        {agent.bio && (
          <p className="text-sm text-muted-foreground line-clamp-3">
            {agent.bio}
          </p>
        )}
        <span className="text-xs text-muted-foreground mt-2 inline-block">
          Click for full profile →
        </span>
      </div>
    </button>
  );
}
