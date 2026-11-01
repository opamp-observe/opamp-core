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

"""Config classifier package for catalog-service file recognition."""

from catalog_service.config_classifiers.composite_classifier import CompositeConfigClassifier
from catalog_service.config_classifiers.config_classifier import (
    ConfigClassification,
    ConfigClassifier,
)
from catalog_service.config_classifiers.fluentbit_classic_classifier import (
    FluentBitClassicConfigClassifier,
)
from catalog_service.config_classifiers.fluentbit_yaml_classifier import (
    FluentBitYamlConfigClassifier,
)
from catalog_service.config_classifiers.fluentd_classifier import FluentdConfigClassifier
from catalog_service.config_classifiers.json_config_classifier import JsonConfigClassifier

__all__ = [
    "CompositeConfigClassifier",
    "ConfigClassification",
    "ConfigClassifier",
    "FluentBitClassicConfigClassifier",
    "FluentBitYamlConfigClassifier",
    "FluentdConfigClassifier",
    "JsonConfigClassifier",
]
