import { useEffect, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { fetchAgents, type Agent } from "@/services/agents";
import type { PageSection } from "../PageBuilder";

interface Step {
  label?: string | null;
  description?: string | null;
  agentRole?: string | null;
}

interface PipelineStepsSectionData {
  heading?: string | null;
  steps?: Step[] | null;
}

export function PipelineSteps({ section }: { section: PageSection }) {
  const data = section as PipelineStepsSectionData;
  const steps = data.steps ?? [];
  const [agents, setAgents] = useState<Agent[]>([]);

  useEffect(() => {
    fetchAgents("all")
      .then(setAgents)
      .catch(() => setAgents([]));
  }, []);

  const getAgentForRole = (role: string | null | undefined) =>
    agents.find(
      (a) =>
        role &&
        (a.title?.toLowerCase() === role.toLowerCase() ||
          a.display_name?.toLowerCase() === role.toLowerCase())
    );

  if (steps.length === 0) return null;

  return (
    <section className="py-16 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        {data.heading && (
          <h2 className="font-display text-2xl font-bold text-foreground mb-12 text-center">
            {data.heading}
          </h2>
        )}
        <div className="max-w-3xl mx-auto space-y-8">
          {steps.map((step, i) => {
            const agent = getAgentForRole(step.agentRole);
            return (
              <div key={i} className="flex gap-6 items-start">
                <div className="flex-shrink-0 w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center font-display font-bold text-primary">
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-display text-lg font-semibold text-foreground">{step.label}</h3>
                    {agent && (
                      <div className="flex items-center gap-2">
                        <Avatar className="h-8 w-8">
                          <AvatarImage
                            src={
                              agent.avatar_image_url ?? agent.avatar_video_url ?? undefined
                            }
                          />
                          <AvatarFallback className="text-xs">
                            {agent.display_name.charAt(0)}
                          </AvatarFallback>
                        </Avatar>
                        <span className="text-sm text-muted-foreground">
                          {agent.display_name}
                        </span>
                      </div>
                    )}
                  </div>
                  {step.description && (
                    <p className="text-muted-foreground">{step.description}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
