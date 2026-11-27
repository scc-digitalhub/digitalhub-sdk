# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""
Protocol constants shared with DigitalHub Core and its auth server.

These are fixed by the backend contract, not tunable per client: tunable
values live in ``ClientConfig``.
"""

from __future__ import annotations

# DHCore REST API paths
API_BASE = "/api/v1"
API_CONTEXT = "/api/v1/-"
API_AUTH_CHECK = "/api/auth"
WELL_KNOWN_CONFIGURATION = "/.well-known/configuration"

# DHCore API levels supported by this library
MIN_API_LEVEL = 16
MAX_API_LEVEL = 20
LIB_API_LEVEL = 16

# Key of the Kubernetes resource profiles in the backend configuration
K8S_RESOURCE_PROFILES_KEY = "k8s_resource_profiles"

# OpenID discovery path on the issuer
WELL_KNOWN_OPENID_CONFIGURATION = "/.well-known/openid-configuration"

# OAuth2 refresh token grant
OAUTH2_GRANT_TYPE = "refresh_token"
OAUTH2_SCOPE = "credentials"

# Personal access token exchange
PAT_SUBJECT_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:pat"
PAT_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:token-exchange"
PAT_SCOPE = "credentials"

# Header that tells the proxy in front of the cluster (DHCORE_PROXY) which service to reach.
PROXY_HOST_HEADER = "X-Proxy-Host"

# Prefixes stripped from credential keys returned by the auth server
DHCORE_PREFIX = "dhcore_"
OAUTH2_PREFIX = "oauth2_"
