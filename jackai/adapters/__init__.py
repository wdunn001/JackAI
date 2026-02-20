"""Channel adapters (web widget, telegram, etc.)."""

from jackai.adapters.base import ChannelAdapterBase
from jackai.adapters.web_widget import WebWidgetAdapter

__all__ = ["ChannelAdapterBase", "WebWidgetAdapter"]
