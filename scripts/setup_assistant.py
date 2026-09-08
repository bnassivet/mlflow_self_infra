"""Configure the MLflow Assistant for a Dockerised server.

Why this exists
---------------
The assistant API is localhost-only by design (it can run the MLflow CLI and edit
code). Behind Docker the browser is never seen as localhost -- Docker's port proxy
rewrites the source address, so `_is_localhost()` in mlflow/server/assistant/api.py
sees the bridge gateway and every call 403s with "You do not have permission to
access this resource".

MLFLOW_ENABLE_REMOTE_ASSISTANT=true lifts that, but only for providers declaring
`allows_remote_access` -- in practice "MLflow AI Gateway". And `PUT /config` and
`POST /skills/install` carry the DENY policy, meaning they stay blocked from a
browser no matter what. So provider selection has to be done server-side: that is
what this script does.

Run it INSIDE the mlflow container:

    docker compose exec mlflow python /scripts/setup_assistant.py \
        --base-url http://host.docker.internal:11434/v1 --model gpt-oss:20b
"""

import argparse
import os

import mlflow
from mlflow.assistant.config import AssistantConfig, ProviderConfig
from mlflow.assistant.providers.mlflow_gateway import MlflowGatewayProvider
from mlflow.entities.gateway_endpoint import (
    GatewayEndpointModelConfig,
    GatewayModelLinkageType,
)
from mlflow.exceptions import MlflowException
from mlflow.protos.databricks_pb2 import RESOURCE_DOES_NOT_EXIST, ErrorCode
from mlflow.tracking._tracking_service.utils import _get_store

NOT_FOUND = ErrorCode.Name(RESOURCE_DOES_NOT_EXIST)


def get_or_create(getter, creator):
    """Idempotency helper: the gateway store raises RESOURCE_DOES_NOT_EXIST rather
    than returning None, and only that error means "safe to create"."""
    try:
        return getter()
    except MlflowException as e:
        if e.error_code != NOT_FOUND:
            raise
        return creator()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="assistant-local-llm")
    parser.add_argument(
        "--base-url",
        default="http://host.docker.internal:11434/v1",
        help="OpenAI-compatible base URL (Ollama's /v1 shim, LM Studio, vLLM...).",
    )
    parser.add_argument("--model", default="gpt-oss:20b")
    parser.add_argument(
        "--api-key",
        default="ollama",
        help="Vanilla Ollama is auth-free but the gateway requires a non-empty key.",
    )
    args = parser.parse_args()

    # `mlflow server` gets its store from --backend-store-uri, but a plain
    # `docker compose exec` inherits no tracking URI and would silently fall back to
    # a throwaway local SQLite file -- writing the gateway endpoint somewhere the
    # running server never reads. DB_URI is set on the service in docker-compose.yml.
    if tracking_uri := os.environ.get("MLFLOW_TRACKING_URI") or os.environ.get("DB_URI"):
        mlflow.set_tracking_uri(tracking_uri)
    else:
        raise SystemExit("Set MLFLOW_TRACKING_URI or DB_URI to the server's backend store.")

    store = _get_store()

    # The gateway talks to any OpenAI-compatible server by using the "openai"
    # provider with an api_base override (see _build_provider_config in
    # mlflow/server/gateway_api.py), so Ollama needs no dedicated provider.
    # api_base lives in the secret's `auth_config`, NOT in `secret_value` -- see
    # _build_endpoint_config in mlflow/server/gateway_api.py, which reads api_key from
    # secret_value and api_base from auth_config. Putting it in secret_value silently
    # leaves api_base unset and the gateway calls api.openai.com instead.
    auth_config = {"api_base": args.base_url}
    secret = get_or_create(
        lambda: store.get_secret_info(secret_name=args.name),
        lambda: store.create_gateway_secret(
            secret_name=args.name,
            secret_value={"api_key": args.api_key},
            provider="openai",
            auth_config=auth_config,
        ),
    )
    # Re-apply on every run so changing --base-url/--api-key takes effect.
    store.update_gateway_secret(
        secret_id=secret.secret_id,
        secret_value={"api_key": args.api_key},
        auth_config=auth_config,
    )
    model_definition = get_or_create(
        lambda: store.get_gateway_model_definition(name=args.name),
        lambda: store.create_gateway_model_definition(
            name=args.name,
            secret_id=secret.secret_id,
            provider="openai",
            model_name=args.model,
        ),
    )
    # get_or_create returns the *existing* definition untouched, so re-apply the model
    # name to make --model meaningful on a second run.
    if model_definition.model_name != args.model:
        model_definition = store.update_gateway_model_definition(
            model_definition_id=model_definition.model_definition_id,
            model_name=args.model,
        )

    endpoint = get_or_create(
        lambda: store.get_gateway_endpoint(name=args.name),
        lambda: store.create_gateway_endpoint(
            name=args.name,
            model_configs=[
                GatewayEndpointModelConfig(
                    model_definition_id=model_definition.model_definition_id,
                    linkage_type=GatewayModelLinkageType.PRIMARY,
                )
            ],
        ),
    )
    print(f"Gateway endpoint ready: {endpoint.name}")

    # Select the gateway provider. Its `model` is the *endpoint* name, since the
    # gateway resolves the concrete model from the endpoint's model definition.
    provider = MlflowGatewayProvider.GATEWAY_PROVIDER_NAME
    config = AssistantConfig.load()
    for name, existing in config.providers.items():
        existing.selected = name == provider
    config.providers.setdefault(provider, ProviderConfig())
    config.providers[provider].selected = True
    config.providers[provider].model = endpoint.name
    config.save()
    print(f"Assistant provider set to {provider!r} using model {endpoint.name!r}")


if __name__ == "__main__":
    main()
