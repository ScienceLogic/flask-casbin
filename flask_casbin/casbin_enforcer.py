"""flask-casbin: Flask module for using Casbin with flask apps
"""
import casbin
from flask import request, jsonify
from functools import wraps

from flask_casbin.utils import authorization_decoder, UnSupportedAuthType


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

    def set_watcher(self, watcher):
        """
        Set the watcher to use with the underlying casbin enforcer
        Args:
            watcher (object):
        Returns:
            None
        """
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
                if header in request.headers:
                    # Make Authorization Header Parser standard
                    if header == "Authorization":
                        # Get Auth Value then decode and parse for owner
                        try:
                            owner = authorization_decoder(request.headers.get(header))
                        except UnSupportedAuthType:
                            # Continue if catch unsupported type in the event of
                            # Other headers needing to be checked
                            self.app.logger.info(
                                "Authorization header type requested for "
                                "decoding is unsupported by flask-casbin at this time"
                            )
                            continue
                        if self.e.enforce(owner, str(request.url_rule), request.method):
                            return func(*args, **kwargs)
                    else:
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

    def update(self):
        """
        Watcher interface as it should be implemented for flask-casbin
        Returns:
            None
        """
        pass

    def set_update_callback(self):
        """
        Set the update callback to be used when an update is detected
        Returns:
            None
        """
        pass

    def try_reload(self):
        """
        Method which checks if there is an update necessary for the casbin
        roles. This is called with each flask request.
        Returns:
            None
        """
        pass
