"""Context manager stub used by cognitive package exports."""


class ContextManager:
    def manage(self, context=None, **kwargs):
        return context or {}
