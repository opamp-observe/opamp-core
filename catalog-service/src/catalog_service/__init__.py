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

"""Standalone catalog-service component package."""

from catalog_service.app import create_app, register_catalog_component
from catalog_service.config_classifiers import (
    CompositeConfigClassifier,
    ConfigClassification,
    ConfigClassifier,
    FluentBitClassicConfigClassifier,
    FluentBitYamlConfigClassifier,
    FluentdConfigClassifier,
)
from catalog_service.config import (
    CATALOG_COMPONENT_ENTRY_POINT,
    CatalogSource,
    CatalogServiceConfig,
    catalog_component_entry_from_payload,
    load_catalog_service_config,
)
from catalog_service.routes import register_catalog_routes
from catalog_service.service import CatalogFileIndexService

__all__ = [
    "CATALOG_COMPONENT_ENTRY_POINT",
    "CompositeConfigClassifier",
    "ConfigClassification",
    "ConfigClassifier",
    "CatalogFileIndexService",
    "CatalogSource",
    "CatalogServiceConfig",
    "FluentBitClassicConfigClassifier",
    "FluentBitYamlConfigClassifier",
    "FluentdConfigClassifier",
    "catalog_component_entry_from_payload",
    "create_app",
    "load_catalog_service_config",
    "register_catalog_component",
    "register_catalog_routes",
]
