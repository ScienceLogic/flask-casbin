"""flask-casbin: Flask module for using Casbin with flask apps
"""
import casbin
from flask import request, jsonify
from functools import wraps


class CasbinEnforcer:
    """
    Casbin Enforce decorator
    """

    e = None

    def __init__(self, app, adapter, watcher=None):
        """
        Args:
            app (object): Flask App object to get Casbin Model
            adapter (object): Casbin Adapter
        """
        self.app = app
        self.adapter = adapter
        self.e = casbin.Enforcer(app.config.get("CASBIN_MODEL"), self.adapter, True)
        if watcher:
            self.e.set_watcher(watcher)

    def enforcer(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.e.watcher:
                self.e.watcher.try_reload()
            # Check sub, obj act against Casbin polices
            self.app.logger.debug(
                "Enforce Headers Config: %s\nRequest Headers: %s"
                % (self.app.config.get("CASBIN_OWNER_HEADERS"), request.headers)
            )
            for header in self.app.config.get("CASBIN_OWNER_HEADERS"):
                if request.headers.has_key(header):
                    for owner in request.headers.getlist(header):
                        self.app.logger.debug(
                            "Enforce against owner: %s header: %s"
                            % (owner.strip('"'), header)
                        )
                        if self.e.enforce(
                            owner.strip('"'), str(request.url_rule), request.method
                        ):
                            return func(*args, **kwargs)
            else:
                return (jsonify({"message": "Unauthorized"}), 401)

        return wrapper

    def manager(self, func):
        """Get the Casbin Enforcer Object to manager Casbin"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(self.e, *args, **kwargs)

        return wrapper

class Watcher:
    """
    Watcher interface as it should be implemented for flask-casbin
    """

    def __init__(self):
        pass

    def update(self):
        """
        Called when the casbin enforcer is updated
        :return:
        """
        pass

    def set_update_callback(self):
        """
        Set the update callback to be used when an update is detected
        :return:
        """
        pass

    def try_reload(self):
        """
        Method which checks if there is an update necessary for the casbin
        roles. This is called with each flask request.
        :return:
        """
        pass