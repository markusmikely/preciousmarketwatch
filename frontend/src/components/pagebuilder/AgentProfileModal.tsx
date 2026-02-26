import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import type { Agent } from "@/services/agents";

interface AgentProfileModalProps {
  agent: Agent | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AgentProfileModal({
  agent,
  open,
  onOpenChange,
}: AgentProfileModalProps) {
  if (!agent) return null;

  const avatarUrl = agent.avatar_image_url ?? agent.avatar_video_url ?? null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex gap-6 items-start">
            <div className="flex-shrink-0 w-24 h-24 rounded-xl overflow-hidden bg-muted">
              <Avatar className="w-full h-full rounded-none">
                <AvatarImage src={avatarUrl ?? undefined} alt={agent.display_name} />
                <AvatarFallback className="rounded-none text-3xl text-primary/70">
                  {agent.display_name.charAt(0)}
                </AvatarFallback>
              </Avatar>
            </div>
            <div className="flex-1 min-w-0">
              <DialogTitle className="text-xl">
                {agent.display_name}
              </DialogTitle>
              <p className="text-primary font-medium mt-0.5">{agent.title}</p>
              <p className="text-sm text-muted-foreground mt-1">{agent.role}</p>
              {agent.tier && (
                <span className="inline-block mt-2 px-2 py-0.5 text-xs font-medium rounded bg-primary/10 text-primary">
                  {agent.tier}
                </span>
              )}
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6 mt-6">
          {agent.bio && (
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-2">Bio</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {agent.bio}
              </p>
            </div>
          )}

          {agent.personality && (
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-2">
                Personality
              </h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {agent.personality}
              </p>
            </div>
          )}

          {agent.quirks && agent.quirks.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-2">
                Quirks
              </h4>
              <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                {agent.quirks.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </div>
          )}

          {agent.specialisms && agent.specialisms.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-2">
                Specialisms
              </h4>
              <div className="flex flex-wrap gap-2">
                {agent.specialisms.map((s, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 text-xs rounded-md bg-muted text-muted-foreground"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {agent.status === "in-development" && agent.eta && (
            <p className="text-sm text-muted-foreground italic">
              Coming in {agent.eta}
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
