# agents/nodes/media.py
import httpx
import base64
from agents.db.queries import store_media_record
from agents.base import publish_event

async def run(state: PipelineState) -> PipelineState:
    run_id  = state["run_id"]
    content = state["content_output"]
    topic   = state["topic"]

    await publish_event("stage.started", {
        "run_id": run_id, "stage": "media"
    })

    media_results = []
    total_cost    = 0.0

    # ── 1. Featured image ─────────────────────────────────────
    try:
        image_prompt = build_image_prompt(content["title"], topic)
        image_url, img_cost = await generate_image(image_prompt)
        wp_media_id  = await upload_to_wp_media(image_url, content["title"])

        media_results.append({
            "type":       "featured_image",
            "wp_media_id": wp_media_id,
            "cost_usd":   img_cost,
        })
        total_cost += img_cost

        await store_media_record(run_id, "featured_image", image_prompt,
                                 wp_media_id, img_cost)
    except Exception as e:
        # Media failure is non-blocking — article still publishes without image
        await publish_event("media.warning", {
            "run_id": run_id, "type": "featured_image", "error": str(e)
        })

    # ── 2. Infographic (if planning flagged it as eligible) ───
    if content.get("infographic_eligible"):
        try:
            infographic_svg = await generate_infographic(
                content.get("infographic_data", {})
            )
            wp_media_id = await upload_svg_to_wp(infographic_svg,
                                                  content["title"])
            media_results.append({
                "type":        "infographic",
                "wp_media_id":  wp_media_id,
                "cost_usd":    0.0,  # SVG render is free
            })
            await store_media_record(run_id, "infographic", None,
                                     wp_media_id, 0.0)
        except Exception as e:
            await publish_event("media.warning", {
                "run_id": run_id, "type": "infographic", "error": str(e)
            })

    await publish_event("stage.complete", {
        "run_id": run_id, "stage": "media",
        "media_count": len(media_results), "cost_usd": total_cost
    })

    return {
        **state,
        "media_output": {"items": media_results, "total_cost": total_cost},
        "current_stage": "media",
        "model_usage": state["model_usage"] + [{
            "agent": "media", "cost_usd": total_cost
        }],
    }


def build_image_prompt(title: str, topic: dict) -> str:
    """
    Build a DALL-E 3 prompt for a financial/investment featured image.
    Avoids text in images (DALL-E renders text poorly).
    Uses abstract, premium financial photography style.
    """
    category_style = {
        "gold":      "gleaming gold bars and coins arranged on dark velvet, professional financial photography, dramatic side lighting",
        "silver":    "polished silver coins and bullion bars, cool tones, professional studio lighting",
        "platinum":  "platinum ingots with subtle metallic sheen, minimalist composition, premium look",
        "gemstones": "precious gemstones in elegant display, macro photography, rich colours",
    }.get(topic["topic_category"], "precious metals in professional studio photography")

    return (
        f"Premium financial photography for an article about: {title}. "
        f"Style: {category_style}. "
        f"No text or words in the image. Suitable for a financial news website. "
        f"High resolution, editorial quality, wide crop suitable for a blog header."
    )


async def generate_image(prompt: str) -> tuple[str, float]:
    """Generate image via DALL-E 3. Returns (url, cost_usd)."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
            json={
                "model":   "dall-e-3",
                "prompt":  prompt,
                "n":       1,
                "size":    "1792x1024",  # landscape for blog headers
                "quality": "standard",  # $0.040/image — use "hd" for hero images
            },
            timeout=60.0
        )
        data = response.json()
        return data["data"][0]["url"], 0.040  # standard quality cost


async def generate_infographic(data: dict) -> str:
    """
    Generate an SVG infographic from structured data.
    Currently supports: comparison tables, step-by-step processes, stat highlights.
    Returns SVG string.
    """
    infographic_type = data.get("type", "stats")

    if infographic_type == "comparison":
        return render_comparison_svg(data["items"], data["title"])
    elif infographic_type == "steps":
        return render_steps_svg(data["steps"], data["title"])
    elif infographic_type == "stats":
        return render_stats_svg(data["stats"], data["title"])
    else:
        raise ValueError(f"Unknown infographic type: {infographic_type}")