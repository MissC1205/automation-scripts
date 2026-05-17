#!/bin/bash
# Fetch detailed info from GitHub API for specific repositories

echo "=== GitHub Repository Details ==="
echo ""

# Array of repo full names to check
repos=(
  "ColorlibHQ/gentelella"
  "coreui/coreui-free-bootstrap-admin-template"
  "tabler/tabler"
  "PanJiaChen/vue-element-admin"
  "BootstrapDash/StarAdmin"
  "creativetimofficial/material-dashboard"
  "agenciaego/pulse"
  "dashboardpack/architectui-html-html-pro"
  "pixincer/frest-html-admin-template"
  "moru Men's/moru Men's"
)

for repo in "${repos[@]}"; do
  echo "--- $repo ---"
  curl -s "https://api.github.com/repos/$repo" | python3 -c "
import sys,json
try:
    d = json.load(sys.stdin)
    if 'message' in d and d['message'] == 'Not Found':
        print('  NOT FOUND')
    else:
        print(f'  Stars: {d.get(\"stargazers_count\",0):,}')
        print(f'  Forks: {d.get(\"forks_count\",0):,}')
        print(f'  Description: {d.get(\"description\",\"N/A\")}')
        print(f'  URL: {d.get(\"html_url\",\"N/A\")}')
        print(f'  Language: {d.get(\"language\",\"N/A\")}')
except Exception as e:
    print(f'  Error: {e}')
" 2>/dev/null
  echo ""
done
