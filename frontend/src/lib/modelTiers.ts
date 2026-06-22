export type ChatTier = "fast" | "balanced" | "deep";

export const CHAT_TIERS: { id: ChatTier; label: string; hint: string }[] = [
  { id: "fast", label: "快速", hint: "省 token，简单问答" },
  { id: "balanced", label: "标准", hint: "默认质量" },
  { id: "deep", label: "深度", hint: "复杂推理" },
];

const FAST_HINTS = ["flash", "lite", "mini", "turbo", "nano", "haiku", "8b", "14b", "air"];
const DEEP_HINTS = ["pro", "max", "ultra", "r1", "opus", "235b", "thinking", "seed-1-8", "sonnet"];

export function resolveTierModel(
  defaultModel: string,
  models: string[],
  tier: ChatTier
): string {
  if (tier === "balanced") return defaultModel;
  const pool = models.length ? models : [defaultModel];
  const hints = tier === "fast" ? FAST_HINTS : DEEP_HINTS;
  for (const h of hints) {
    const hit = pool.find((m) => m.toLowerCase().includes(h));
    if (hit) return hit;
  }
  return defaultModel;
}
