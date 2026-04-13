"""
PanOS connection manager module.

Provides connection handling for Palo Alto Panorama using pan-os-python SDK.
"""

import logging
import time
from typing import Optional, List, Dict, Any
# Import panos lazily to allow testing without the library
try:
    from panos.panorama import Panorama
    from panos.firewall import Firewall
    from panos.errors import PanDeviceError, PanURLError
    _PANOS_AVAILABLE = True
except ImportError:
    Panorama, Firewall, PanDeviceError, PanURLError = None, None, None, None
    _PANOS_AVAILABLE = False
    PanDeviceError = Exception  # Fallback for type checking
    PanURLError = Exception  # Fallback for type checking

from src.utils.logger import get_logger


logger = logging.getLogger(__name__)


class PanOSConnectionError(Exception):
    """Exception raised for PanOS connection errors."""

    def __init__(self, message: str, *args: object):
        super().__init__(message, *args)
        self.message = message


class PanOSConnection:
    """Manages connection to Palo Alto Panorama or Firewall."""

    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 1.0  # seconds
    MAX_RETRY_DELAY = 30.0  # seconds

    def __init__(
        self,
        hostname: str,
        username: str = "admin",
        password: str = None,
        api_key: str = None,
        port: int = 443,
        timeout: int = 30,
        use_ssl: bool = True,
        verify_ssl: bool = True,
    ):
        """
        Initialize PanOS connection.

        Args:
            hostname: Panorama or firewall IP/hostname
            username: Username for authentication
            password: Password for authentication (optional if api_key provided)
            api_key: API key for authentication (optional if password provided)
            port: API port (default: 443)
            timeout: Connection timeout in seconds
            use_ssl: Use SSL for connection
            verify_ssl: Verify SSL certificates
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.api_key = api_key
        self.port = port
        self.timeout = timeout
        self.use_ssl = use_ssl
        self.verify_ssl = verify_ssl

        self._panorama: Optional[Panorama] = None
        self._firewall: Optional[Firewall] = None
        self._connected = False
        self._connection_time: Optional[float] = None

        # Validate authentication method
        if not self.api_key and not self.password:
            raise PanOSConnectionError(
                "Either password or api_key must be provided"
            )

    @property
    def is_connected(self) -> bool:
        """Check if connection is established."""
        return self._connected

    @property
    def connection_time(self) -> Optional[float]:
        """Get connection establishment time."""
        return self._connection_time

    def connect(self) -> bool:
        """
        Establish connection to Panorama.

        Returns:
            True if connection successful

        Raises:
            PanOSConnectionError: If connection fails after retries
        """
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.info(
                    f"Connecting to {self.hostname}:{self.port} (attempt {attempt}/{self.MAX_RETRIES})"
                )

                # Create Panorama instance
                self._panorama = Panorama(
                    hostname=self.hostname,
                    api_key=self.api_key,
                    api_username=self.username,
                    api_password=self.password,
                    port=self.port,
                    timeout=self.timeout,
                    ssl=self.use_ssl,
                    http=False,
                )

                # Test connection
                self._connected = True
                self._connection_time = time.time()

                logger.info(
                    f"Successfully connected to {self.hostname} at {self._connection_time}"
                )
                return True

            except PanDeviceError as e:
                logger.warning(
                    f"Connection attempt {attempt} failed: {str(e)}"
                )
                if attempt < self.MAX_RETRIES:
                    delay = min(
                        self.BASE_RETRY_DELAY * (2 ** (attempt - 1)),
                        self.MAX_RETRY_DELAY,
                    )
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise PanOSConnectionError(
                        f"Failed to connect to {self.hostname} after {self.MAX_RETRIES} attempts"
                    ) from e

        return False

    def disconnect(self) -> bool:
        """
        Close the connection.

        Returns:
            True if disconnection successful
        """
        try:
            if self._panorama:
                # Clean up any resources
                self._panorama = None
            self._connected = False
            logger.info("Connection closed")
            return True
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            return False

    def get_panorama(self) -> Panorama:
        """
        Get the Panorama instance.

        Returns:
            Panorama instance

        Raises:
            PanOSConnectionError: If not connected
        """
        if not self._connected or self._panorama is None:
            raise PanOSConnectionError(
                "Not connected to Panorama. Call connect() first."
            )
        return self._panorama

    def get_firewall(self, serial_number: str) -> Firewall:
        """
        Get a specific firewall instance.

        Args:
            serial_number: Firewall serial number

        Returns:
            Firewall instance

        Raises:
            PanOSConnectionError: If not connected or firewall not found
        """
        if not self._connected or self._panorama is None:
            raise PanOSConnectionError(
                "Not connected to Panorama. Call connect() first."
            )

        # Search for the firewall
        firewalls = self._panorama.refresh_devices()
        for fw in firewalls:
            if fw.serial == serial_number:
                self._firewall = fw
                return self._firewall

        raise PanOSConnectionError(
            f"Firewall with serial {serial_number} not found"
        )

    def set_api_key(self, api_key: str) -> None:
        """Set API key for authentication."""
        self.api_key = api_key
        self.password = None  # Clear password if using API key

    def test_connection(self) -> bool:
        """
        Test if connection is still valid.

        Returns:
            True if connection is valid
        """
        if not self._panorama:
            return False

        try:
            self._panorama.op("show system info")
            return True
        except Exception:
            return False

    def execute_op(self, cmd: str, vsys: str = "vsys1") -> Dict[str, Any]:
        """
        Execute an operational command.

        Args:
            cmd: Operational command to execute
            vsys: Virtual system (default: vsys1)

        Returns:
            Command result as dictionary

        Raises:
            PanOSConnectionError: If connection fails
        """
        if not self._connected:
            raise PanOSConnectionError("Not connected to Panorama")

        try:
            result = self._panorama.op(cmd, vsys=vsys)
            return result
        except PanDeviceError as e:
            raise PanOSConnectionError(f"Command failed: {str(e)}") from e

    def commit(self, sync: bool = True, force: bool = False) -> bool:
        """
        Commit configuration to Panorama.

        Args:
            sync: Wait for commit to complete
            force: Force commit even if others are in progress

        Returns:
            True if commit successful

        Raises:
            PanOSConnectionError: If commit fails
        """
        if not self._connected:
            raise PanOSConnectionError("Not connected to Panorama")

        try:
            result = self._panorama.commit(sync=sync, force=force)
            return result
        except PanDeviceError as e:
            raise PanOSConnectionError(f"Commit failed: {str(e)}") from e

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False  # Don't suppress exceptions


class ConnectionPool:
    """Manages multiple PanOS connections."""

    def __init__(self, max_connections: int = 5):
        """
        Initialize connection pool.

        Args:
            max_connections: Maximum number of connections
        """
        self.max_connections = max_connections
        self._connections: List[PanOSConnection] = []
        self._lock = None  # Would use threading.Lock for async

    def get_connection(self, **kwargs) -> PanOSConnection:
        """
        Get a connection from the pool or create new one.

        Args:
            **kwargs: Connection parameters

        Returns:
            PanOSConnection instance
        """
        if len(self._connections) >= self.max_connections:
            # Reuse oldest connection
            return self._connections.pop(0)

        conn = PanOSConnection(**kwargs)
        self._connections.append(conn)
        return conn

    def release_connection(self, conn: PanOSConnection) -> None:
        """Release connection back to pool."""
        if conn in self._connections:
            conn.disconnect()
            self._connections.remove(conn)

    def close_all(self) -> None:
        """Close all connections in the pool."""
        for conn in self._connections:
            try:
                conn.disconnect()
            except Exception:
                pass
        self._connections.clear()