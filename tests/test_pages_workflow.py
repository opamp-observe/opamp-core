# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Contract tests for the main-branch GitHub Pages deployment workflow."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "deploy_pages.yml"


def test_pages_workflow_builds_docs_only_from_main() -> None:
    """Publish the Jekyll documentation only after relevant main-branch changes."""
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "push:" in workflow
    assert "- main" in workflow
    assert "- \"docs/**\"" in workflow
    assert "workflow_dispatch:" in workflow
    assert workflow.count("if: github.ref == 'refs/heads/main'") == 2
    assert "gem install bundler --version 4.0.22 --no-document" in workflow
    assert "bundle exec jekyll build --destination ../_site" in workflow
    assert "actions/upload-pages-artifact@v4" in workflow
    assert "actions/deploy-pages@v4" in workflow
    assert "pages: write" in workflow
    assert "id-token: write" in workflow
