#!/bin/bash
# Search for specific popular admin dashboard templates with frontend + backend

echo "=== Searching Popular Admin Dashboard Templates ==="
echo ""

# 1. AdminLTE - popular Bootstrap admin template
echo "1. Searching for AdminLTE..."
curl -s "https://api.github.com/search/repositories?q=AdminLTE+admin+dashboard+template" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Found: {d.get(\"total_count\",0)} repos')" 2>/dev/null || echo "API search skipped"

# 2. Tabler
echo ""
echo "2. Searching for Tabler..."
curl -s "https://api.github.com/repos/tabler/tabler" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Stars: {d.get(\"stargazers_count\",0)}, Description: {d.get(\"description\",\"\")}')" 2>/dev/null || echo "Direct search"

# 3. CoreUI
echo ""
echo "3. Searching for CoreUI..."
curl -s "https://api.github.com/repos/coreui/coreui-free-bootstrap-admin-template" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Stars: {d.get(\"stargazers_count\",0)}, Description: {d.get(\"description\",\"\")}')" 2>/dev/null || echo "Direct search"

# 4. Gentelella
echo ""
echo "4. Searching for Gentelella..."
curl -s "https://api.github.com/repos/ColorlibHQ/gentelella" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Stars: {d.get(\"stargazers_count\",0)}, Description: {d.get(\"description\",\"\")}')" 2>/dev/null || echo "Direct search"

# 5. StarAdmin
echo ""
echo "5. Searching for StarAdmin..."
curl -s "https://api.github.com/repos/BootstrapDash/StarAdmin" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Stars: {d.get(\"stargazers_count\",0)}, Description: {d.get(\"description\",\"\")}')" 2>/dev/null || echo "Direct search"

# 6. Material Dashboard
echo ""
echo "6. Searching for Material Dashboard..."
curl -s "https://api.github.com/repos/creativetimofficial/material-dashboard" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Stars: {d.get(\"stargazers_count\",0)}, Description: {d.get(\"description\",\"\")}')" 2>/dev/null || echo "Direct search"

# 7. Pulse Admin
echo ""
echo "7. Searching for Pulse..."
curl -s "https://api.github.com/repos/agenciaego/pulse" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Stars: {d.get(\"stargazers_count\",0)}, Description: {d.get(\"description\",\"\")}')" 2>/dev/null || echo "Direct search"

# 8. ArchitectUI
echo ""
echo "8. Searching for ArchitectUI..."
curl -s "https://api.github.com/repos/dashboardpack/architectui-html-html-pro" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Stars: {d.get(\"stargazers_count\",0)}, Description: {d.get(\"description\",\"\")}')" 2>/dev/null || echo "Direct search"

# 9. Frest Admin
echo ""
echo "9. Searching for Frest..."
curl -s "https://api.github.com/repos/pixincer/frest-html-admin-template" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Stars: {d.get(\"stargazers_count\",0)}, Description: {d.get(\"description\",\"\")}')" 2>/dev/null || echo "Direct search"

# 10. Vue Element Admin (has frontend + backend)
echo ""
echo "10. Searching for Vue Element Admin..."
curl -s "https://api.github.com/repos/PanJiaChen/vue-element-admin" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Stars: {d.get(\"stargazers_count\",0)}, Description: {d.get(\"description\",\"\")}')" 2>/dev/null || echo "Direct search"

echo ""
echo "=== Done ==="
