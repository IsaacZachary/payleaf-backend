class BaseKycProvider:
    """
    Abstract base class for KYC providers (Onfido, Sumsub, Veriff).
    """
    def submit_business_profile(self, business_profile):
        """Dispatches profile data to the provider."""
        raise NotImplementedError

    def verify_webhook_signature(self, payload, signature):
        """Validates incoming webhook from the provider."""
        raise NotImplementedError

    def handle_callback(self, data):
        """Processes verification results from the provider callback."""
        raise NotImplementedError
