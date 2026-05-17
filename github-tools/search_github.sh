#!/bin/bash
# Search GitHub API for business website templates with admin panel

echo "=== Searching GitHub for Business Website Templates ==="
echo ""

# Search 1: website template with admin panel
echo "Search 1: website template with admin panel"
curl -s "https://api.github.com/search/repositories?q=website+template+admin+panel&sort=stars&order=desc&per_page=10" | grep -E '"full_name"|"stargazers_count"|"description"|"html_url"' | head -20
echo ""

# Search 2: business website HTML CSS JS
echo "Search 2: business website HTML CSS JS"
curl -s "https://api.github.com/search/repositories?q=business+website+HTML+CSS+JS&sort=stars&order=desc&per_page=10" | grep -E '"full_name"|"stargazers_count"|"description"|"html_url"' | head -20
echo ""

# Search 3: admin dashboard template business
echo "Search 3: admin dashboard template business"
curl -s "https://api.github.com/search/repositories?q=admin+dashboard+template+business&sort=stars&order=desc&per_page=10" | grep -E '"full_name"|"stargazers_count"|"description"|"html_url"' | head -20
echo ""

# Search 4: company website template with backend
echo "Search 4: company website template with backend"
curl -s "https://api.github.com/search/repositories?q=company+website+template+backend&sort=stars&order=desc&per_page=10" | grep -E '"full_name"|"stargazers_count"|"description"|"html_url"' | head -20
echo ""

# Search 5: admin panel frontend backend
echo "Search 5: admin panel frontend backend"
curl -s "https://api.github.com/search/repositories?q=admin+panel+frontend+backend&sort=stars&order=desc&per_page=10" | grep -E '"full_name"|"stargazers_count"|"description"|"html_url"' | head -20
