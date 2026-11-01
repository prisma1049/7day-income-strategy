#!/usr/bin/env python3
"""
X/Twitter posting script for the GPU comparison article.
Run after xurl authentication is complete.
"""

import subprocess
import json
import time

# Thread content
THREAD = [
    """🧵 GPU Cloud Price War 2026: RunPod vs Vast.ai vs Lambda Labs

Tested all three for AI training this week. The winner depends entirely on your use case.

TL;DR: RunPod for devs (20% recurring affiliate), Vast.ai for budget, Lambda for prod (no affiliate).

Thread 👇""",

    """RunPod 🥇 Best DX for developers
• RTX 4090: $0.34/hr | A100: $1.19/hr | H100: $2.69/hr
• Per-second billing, serverless inference endpoints
• runpodctl CLI + GitHub Actions CI/CD
• Templates: vLLM, PyTorch, ComfyUI, SDXL
• 20% recurring commission, 60-day cookie""",

    """Vast.ai 💰 Cheapest raw GPU (marketplace)
• RTX 4090: $0.25-0.45/hr | A100: $1.10-1.80/hr
• P2P marketplace = variable quality, no SLA
• "Interruptible" instances up to 50% off
• 10% commission, 30-day cookie
• Good for: single runs, experiments, budget projects""",

    """Lambda Labs 🏢 Professional choice
• RTX 4090: $0.60-0.80/hr | A100: $1.50-2.00/hr
• Own DCs, Lambda Stack (optimized ML env), enterprise SLA
• ❌ NO public affiliate program
• Best for: production workloads, teams needing stability, zero-ops""",

    """Real cost example: 1 week fine-tuning (8×A100, 24/7)
• RunPod: ~$1,600 → ~$320 recurring affiliate commission
• Vast.ai: ~$1,480-2,420 → ~$148-242 commission
• Lambda: ~$2,000-2,700 → $0 (no program)

Full breakdown + decision matrix:
https://florian.github.io/7day-income-strategy/runpod-vs-vast-vs-lambda.html?utm_source=twitter&utm_medium=social&utm_campaign=7day_sprint&utm_content=twitter_gpu_comparison""",

    """Part of my 7-day zero-capital affiliate experiment (0€ investment, transparent tracking).

RunPod (20% recurring): https://runpod.io?utm_source=twitter&utm_medium=social&utm_campaign=7day_sprint&utm_content=twitter_gpu_comparison&ref=7day_sprint

Vast.ai (10%): https://vast.ai?utm_source=twitter&utm_medium=social&utm_campaign=7day_sprint&utm_content=twitter_gpu_comparison&ref=7day_sprint

#GPUCloud #AI #MachineLearning #RunPod #VastAI #BuildInPublic"""
]

def post_thread():
    """Post the thread to X/Twitter using xurl."""
    prev_id = None
    
    for i, tweet in enumerate(THREAD):
        print(f"Posting tweet {i+1}/{len(THREAD)}...")
        
        if prev_id:
            # Reply to previous tweet
            cmd = ["xurl", "reply", prev_id, tweet]
        else:
            # First tweet
            cmd = ["xurl", "post", tweet]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"Error posting tweet {i+1}: {result.stderr}")
                return False
            
            # Parse response to get tweet ID
            response = json.loads(result.stdout)
            prev_id = response.get("data", {}).get("id")
            print(f"  ✅ Posted: {prev_id}")
            
            # Rate limit protection
            if i < len(THREAD) - 1:
                time.sleep(2)
                
        except subprocess.TimeoutExpired:
            print(f"Timeout posting tweet {i+1}")
            return False
        except json.JSONDecodeError:
            print(f"Failed to parse response for tweet {i+1}: {result.stdout}")
            return False
        except Exception as e:
            print(f"Error posting tweet {i+1}: {e}")
            return False
    
    print(f"\n✅ Thread posted successfully! First tweet ID: {THREAD[0][:50]}...")
    return True

if __name__ == "__main__":
    # Check auth first
    result = subprocess.run(["xurl", "auth", "status"], capture_output=True, text=True)
    if "oauth2:" in result.stdout and "(none)" not in result.stdout.split("oauth2:")[1].split("\n")[0]:
        print("✅ Authenticated, posting thread...")
        post_thread()
    else:
        print("❌ Not authenticated. Run setup first:")
        print("  xurl auth apps add my-app --client-id YOUR_ID --client-secret YOUR_SECRET")
        print("  xurl auth oauth2 --app my-app YOUR_USERNAME")
        print("  xurl auth default my-app")