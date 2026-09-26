# Remaining organiser details

The supplied PDF confirms AI_API_KEY, root make setup/run/test and text-only evaluation. This is a draft for the team; no message has been sent to organisers.

1. Confirmed September 27: final evaluation uses **DeepSeek and Qwen** families. Which exact model IDs/versions, hosting provider, endpoint, API protocol and authentication scheme should AI_API_KEY use? Will each model be evaluated separately, and how is the selected model supplied?
2. What OS/architecture and Python version are provided? Are make, git, venv, Node and target test dependencies preinstalled?
3. After make run, is task delivery interactive or automated? What exact payload carries the repository, issue and tests? Is the repository already a local checkout or supplied as a URL?
4. What files/results and report format must be returned? Are exit codes prescribed?
5. What network, shell, dependency installation and filesystem access is permitted? Where are held-out tests and protected paths?
6. Are there token/request/time/cost ceilings, efficiency scoring weights or required generation settings?

The model families are now known; remaining details in 1–3 are needed to finalize the committed evaluation profile and perform the true official-environment rehearsal. Current Gemini settings are explicitly provisional.
