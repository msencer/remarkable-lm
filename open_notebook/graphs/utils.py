from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from loguru import logger

from open_notebook.domain.models import model_manager
from open_notebook.models.llms import LanguageModel
from open_notebook.prompter import Prompter
from open_notebook.utils import token_count


def provision_langchain_model(
    content, model_id, default_type, **kwargs
) -> BaseChatModel:
    """
    Returns the best model to use based on the context size and on whether there is a specific model being requested in Config.
    If context > 105_000, returns the large_context_model
    If model_id is specified in Config, returns that model
    Otherwise, returns the default model for the given type
    """
    tokens = token_count(content)

    if tokens > 105_000:
        logger.debug(
            f"Using large context model because the content has {tokens} tokens"
        )
        model = model_manager.get_default_model("large_context", **kwargs)
    elif model_id:
        model = model_manager.get_model(model_id, **kwargs)
    else:
        model = model_manager.get_default_model(default_type, **kwargs)

    assert isinstance(model, LanguageModel), f"Model is not a LanguageModel: {model}"
    return model.to_langchain()


# todo: turn into a graph
def run_pattern(
    pattern_name: str,
    config,
    messages=[],
    state: dict = {},
    parser=None,
) -> BaseMessage:
    system_prompt = Prompter(prompt_template=pattern_name, parser=parser).render(
        data=state
    )
    payload = [system_prompt] + messages
    chain = provision_langchain_model(
        str(payload), config.get("configurable", {}).get("model_id"), "transformation"
    )

    response = chain.invoke(payload)

    return response
