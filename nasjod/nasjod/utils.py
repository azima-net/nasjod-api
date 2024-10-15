from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class InfiniteUserRateThrottle(UserRateThrottle):
    def allow_request(self, request, view):
        if self.get_rate() == 'infinite':
            return True  # No throttling if set to 'infinite'
        return super().allow_request(request, view)

class InfiniteAnonRateThrottle(AnonRateThrottle):
    def allow_request(self, request, view):
        if self.get_rate() == 'infinite':
            return True  # No throttling if set to 'infinite'
        return super().allow_request(request, view)
