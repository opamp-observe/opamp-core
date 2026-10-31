#!/usr/bin/env python3
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
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from config_service.json_utils import load_json_file
from config_service.rule_engine.registry import RuleAdapterRegistry

LOGGER = logging.getLogger(__name__)

UTF8_ENCODING = "utf-8"
KEY_RULESETS = "rulesets"
KEY_PROFILES = "profiles"
KEY_DEFAULT_PROFILE = "default_profile"
KEY_VERSION_OVERRIDES = "version_overrides"
KEY_ADDITIONAL_RULESETS = "additional_rulesets"


class RulesRegistryService:
    """Load, validate, and resolve rule profiles and rulesets from registry files."""

    def __init__(self, registry_path: Path) -> None:
        """Initialize the rules registry service and eagerly load the registry file."""
        self.registry_path = registry_path
        self._registry: dict[str, Any] = {}
        self._adapter_registry = RuleAdapterRegistry()
        self._load()

    def _load(self) -> None:
        """Load the raw registry payload from disk and validate its structure."""
        self._registry = load_json_file(self.registry_path, purpose="validation rules registry")
        self.validate_registry()

    def validate_registry(self) -> None:
        """Validate the registry payload and all referenced rulesets and profiles."""
        if KEY_PROFILES not in self._registry or KEY_RULESETS not in self._registry:
            raise ValueError("validation-rules-registry.json must include 'profiles' and 'rulesets'")

        rulesets = self._registry[KEY_RULESETS]
        if not isinstance(rulesets, dict) or not rulesets:
            raise ValueError("rulesets must be a non-empty object")

        for name, ruleset in rulesets.items():
            if not isinstance(ruleset, dict):
                raise ValueError(f"ruleset '{name}' must be an object")
            self._adapter_registry.validate_ruleset(name, ruleset)

        profiles = self._registry[KEY_PROFILES]
        for profile_name, profile in profiles.items():
            if not isinstance(profile, dict):
                raise ValueError(f"profile '{profile_name}' must be an object")
            for ruleset_name in profile.get(KEY_RULESETS, []):
                if ruleset_name not in rulesets:
                    raise ValueError(
                        f"profile '{profile_name}' references unknown ruleset '{ruleset_name}'"
                    )

    def get_registry(self) -> dict[str, Any]:
        """Return the validated raw rules registry payload."""
        return self._registry

    def get_default_profile(self) -> str:
        """Return the configured default validation profile name."""
        default = self._registry.get(KEY_DEFAULT_PROFILE)
        if not default:
            raise ValueError("default_profile missing from validation rules registry")
        return str(default)

    def get_profile_rulesets(self, profile: str, version: str) -> list[str]:
        """Return the ruleset names that apply to one profile and version."""
        profiles = self._registry.get(KEY_PROFILES, {})
        if profile not in profiles:
            raise KeyError(f"Unknown validation profile: {profile}")

        selected = list(profiles[profile].get(KEY_RULESETS, []))
        version_overrides = self._registry.get(KEY_VERSION_OVERRIDES, {})
        for extra in version_overrides.get(version, {}).get(KEY_ADDITIONAL_RULESETS, []):
            if extra not in selected:
                selected.append(extra)
        return selected

    def get_ruleset(self, ruleset_name: str) -> dict[str, Any]:
        """Return one named ruleset payload from the loaded registry."""
        return self._registry[KEY_RULESETS][ruleset_name]

    @property
    def adapter_registry(self) -> RuleAdapterRegistry:
        """Return the rule adapter registry used for ruleset adapter resolution."""
        return self._adapter_registry
