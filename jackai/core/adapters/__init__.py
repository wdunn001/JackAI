"""Channel adapters (web widget, telegram, etc.)."""

from jackai.core.adapters.base import ChannelAdapterBase
from jackai.core.adapters.web_widget import WebWidgetAdapter

__all__ = ["ChannelAdapterBase", "WebWidgetAdapter"]
