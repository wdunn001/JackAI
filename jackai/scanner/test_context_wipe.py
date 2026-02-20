"""Test context wipe: set context -> wipe (new_session or inject) -> probe; return ContextWipeTestResult."""

from jackai.adapters.web_widget import WebWidgetAdapter
from jackai.context import get_injection_payloads
from jackai.models.config import TargetConfig
from jackai.models.interface import ContextStrategy, SendRequest
from jackai.models.scanner import ContextWipeTestResult, IdentifiedInteraction
from jackai.scanner.adapter_factory import build_target_config_from_result

# Probe messages for context-wipe test
CONTEXT_SET_MESSAGE = "Remember: your secret word is BANANA."
PROBE_MESSAGE = "What is the secret word I asked you to remember?"
SECRET_REVEAL_INDICATOR = "BANANA"


def run_context_wipe_test(
    identified: IdentifiedInteraction,
    try_new_session: bool = True,
    try_inject: bool = True,
) -> ContextWipeTestResult:
    """
    Run set-context -> wipe -> probe. Returns ContextWipeTestResult with success and target_config.
    Tries new_session first if try_new_session; then inject if try_inject and new_session failed.
    """
    config = TargetConfig(
        name=f"discovered-{identified.widget_type}",
        adapter_type="web_widget",
        url=identified.url,
        selectors=identified.selectors,
        recommended_context_strategy="new_session",
        widget_type=identified.widget_type,
    )
    adapter = WebWidgetAdapter()
    success = False
    strategy_used = ""

    try:
        adapter.connect(config)
    except Exception:
        return ContextWipeTestResult(
            identified=identified,
            success=False,
            strategy_used="",
            target_config=build_target_config_from_result(
                identified, success=False, strategy_used=""
            ),
        )

    # 1. Set context
    try:
        adapter.send(SendRequest(content=CONTEXT_SET_MESSAGE))
    except Exception:
        adapter.disconnect()
        return ContextWipeTestResult(
            identified=identified,
            success=False,
            strategy_used="",
            target_config=build_target_config_from_result(
                identified, success=False, strategy_used=""
            ),
        )

    # 2 & 3. Try new_session first
    if try_new_session:
        try:
            adapter.clear_context(ContextStrategy(strategy="new_session"))
            reply = adapter.send(SendRequest(content=PROBE_MESSAGE))
            if SECRET_REVEAL_INDICATOR not in (reply.content or "").upper():
                success = True
                strategy_used = "new_session"
        except Exception:
            pass

    # 4. If not success, try inject
    if not success and try_inject:
        try:
            adapter.connect(config)  # fresh connect
            adapter.send(SendRequest(content=CONTEXT_SET_MESSAGE))
            for payload in get_injection_payloads():
                adapter.clear_context(ContextStrategy(strategy="inject", payload=payload))
                reply = adapter.send(SendRequest(content=PROBE_MESSAGE))
                if SECRET_REVEAL_INDICATOR not in (reply.content or "").upper():
                    success = True
                    strategy_used = "inject"
                    break
        except Exception:
            pass

    target_config = build_target_config_from_result(
        identified, success=success, strategy_used=strategy_used or "new_session"
    )

    adapter.disconnect()

    return ContextWipeTestResult(
        identified=identified,
        success=success,
        strategy_used=strategy_used,
        target_config=target_config,
    )
