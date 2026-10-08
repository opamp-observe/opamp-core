<!--
Copyright 2026 mp3monster.org
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# GitHub Landing Page

This folder contains the standalone project landing page. It remains usable as
a directly rendered HTML page and does not require Jekyll.

Use one of these links to render the current static landing page as a normal web
page:

- Rendered page (RawGitHack): https://raw.githack.com/opamp-observe/opamp-core/main/github-landingpage/index.html
- Rendered page (HTMLPreview): https://htmlpreview.github.io/?https://raw.githubusercontent.com/opamp-observe/opamp-core/main/github-landingpage/index.html

Source file:

- https://github.com/opamp-observe/opamp-core/blob/main/github-landingpage/index.html

## Jekyll

GitHub Pages publishes from the repository's `docs/` directory. The
configuration in `docs/_config.yml` applies the
[jekyll-theme-yat](https://github.com/jeffreytse/jekyll-theme-yat/) remote theme
to the project documentation at `https://opamp.info/`. The repository's GitHub
Pages URL redirects to that custom domain.

```yaml
remote_theme: "jeffreytse/jekyll-theme-yat@v1.10.0"
plugins:
  - jekyll-remote-theme
```

The release is pinned because the current YAT development branch requires a
newer Sass compiler than the GitHub Pages `232` build environment. Validate the
published result locally from the repository root with:

```powershell
$env:BUNDLE_GEMFILE = (Resolve-Path "docs/Gemfile").Path
bundle install
bundle exec github-pages build --source docs --destination build/github-pages-site
```

The canonical project stylesheet is
`docs/assets/css/fluent-opamp.css`. YAT loads it through
`docs/_includes/custom-head.html`, using Jekyll's `relative_url` filter so the
generated URL follows the active Pages base URL.

Mermaid diagram rendering is enabled from `docs/_config.yml` and loaded through
the same custom head include. Markdown fences such as ```` ```mermaid ```` are
converted in the browser by `docs/assets/js/mermaid-loader.js`.

The standalone page continues to load `landing.css`. That file and
`assets/css/fluent-opamp.css` are compatibility wrappers which import the
canonical stylesheet from `docs/`, so the landing page and GitHub Pages share
the same visual rules without duplicating them.
