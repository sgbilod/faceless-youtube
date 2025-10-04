"""
YouTube OAuth2 Authentication Manager

Handles Google OAuth2 authentication flow for YouTube API access:
- OAuth2 web flow with local callback server
- Token storage and encryption
- Automatic token refresh
- Multiple account support
- Credential validation
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pydantic import BaseModel, Field, validator
import keyring
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class AuthStatus(str, Enum):
    """Authentication status"""
    NOT_AUTHENTICATED = "not_authenticated"
    AUTHENTICATED = "authenticated"
    TOKEN_EXPIRED = "token_expired"
    REFRESH_REQUIRED = "refresh_required"
    INVALID_CREDENTIALS = "invalid_credentials"
    ERROR = "error"


@dataclass
class AuthConfig:
    """Authentication configuration"""
    client_secrets_path: str
    token_storage_path: str = "youtube_tokens"
    scopes: List[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ])
    redirect_port: int = 8080
    encrypt_tokens: bool = True
    keyring_service: str = "faceless_youtube"
    auto_refresh: bool = True
    refresh_threshold_minutes: int = 10  # Refresh if token expires in < 10 min


class YouTubeCredentials(BaseModel):
    """YouTube credentials model"""
    account_name: str
    email: Optional[str] = None
    channel_id: Optional[str] = None
    channel_title: Optional[str] = None
    token: str
    refresh_token: Optional[str] = None
    token_uri: Optional[str] = None
    client_id: str
    client_secret: str
    scopes: List[str]
    expiry: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_refreshed: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class AuthManager:
    """
    Manages YouTube OAuth2 authentication
    
    Features:
    - OAuth2 web flow with local callback
    - Token storage with encryption
    - Automatic token refresh
    - Multiple account support
    - Credential validation
    
    Example:
        auth = AuthManager(
            client_secrets_path="client_secrets.json"
        )
        
        # First time authentication
        creds = await auth.authenticate(account_name="main")
        
        # Load existing credentials
        creds = await auth.load_credentials("main")
        
        # Get YouTube API client
        youtube = await auth.get_youtube_client("main")
    """
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.credentials_cache: Dict[str, Credentials] = {}
        self._encryption_key: Optional[bytes] = None
        
        # Create token storage directory
        Path(config.token_storage_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption key
        if config.encrypt_tokens:
            self._init_encryption_key()
    
    def _init_encryption_key(self):
        """Initialize or retrieve encryption key from system keyring"""
        try:
            # Try to get existing key
            key_str = keyring.get_password(
                self.config.keyring_service,
                "encryption_key"
            )
            
            if key_str:
                self._encryption_key = key_str.encode()
            else:
                # Generate new key
                self._encryption_key = Fernet.generate_key()
                keyring.set_password(
                    self.config.keyring_service,
                    "encryption_key",
                    self._encryption_key.decode()
                )
            
            logger.info("Encryption key initialized")
        except Exception as e:
            logger.warning(f"Failed to use keyring, using in-memory key: {e}")
            self._encryption_key = Fernet.generate_key()
    
    def _encrypt(self, data: str) -> str:
        """Encrypt data"""
        if not self.config.encrypt_tokens or not self._encryption_key:
            return data
        
        f = Fernet(self._encryption_key)
        encrypted = f.encrypt(data.encode())
        return encrypted.decode()
    
    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt data"""
        if not self.config.encrypt_tokens or not self._encryption_key:
            return encrypted_data
        
        try:
            f = Fernet(self._encryption_key)
            decrypted = f.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise ValueError("Invalid or corrupted encrypted data")
    
    def _get_token_path(self, account_name: str) -> Path:
        """Get token file path for account"""
        return Path(self.config.token_storage_path) / f"{account_name}.json"
    
    async def authenticate(
        self,
        account_name: str,
        force_new: bool = False
    ) -> YouTubeCredentials:
        """
        Authenticate with YouTube using OAuth2
        
        Args:
            account_name: Name for this account (for multiple account support)
            force_new: Force new authentication even if valid credentials exist
        
        Returns:
            YouTubeCredentials with access token
        
        Raises:
            FileNotFoundError: If client secrets file not found
            ValueError: If authentication fails
        """
        # Check for existing valid credentials
        if not force_new:
            try:
                existing = await self.load_credentials(account_name)
                if existing and await self._validate_credentials(existing):
                    logger.info(f"Using existing valid credentials for {account_name}")
                    return existing
            except FileNotFoundError:
                pass
        
        logger.info(f"Starting OAuth2 flow for {account_name}")
        
        # Start OAuth2 flow
        flow = InstalledAppFlow.from_client_secrets_file(
            self.config.client_secrets_path,
            scopes=self.config.scopes,
            redirect_uri=f"http://localhost:{self.config.redirect_port}/"
        )
        
        # Run local server to handle callback
        # This will open browser for user to authorize
        creds = await asyncio.to_thread(
            flow.run_local_server,
            port=self.config.redirect_port,
            prompt="consent",
            success_message="Authentication successful! You can close this window."
        )
        
        # Get channel info
        youtube = build("youtube", "v3", credentials=creds)
        channel_info = await self._get_channel_info(youtube)
        
        # Create credentials object
        yt_creds = YouTubeCredentials(
            account_name=account_name,
            email=channel_info.get("email"),
            channel_id=channel_info.get("channel_id"),
            channel_title=channel_info.get("channel_title"),
            token=creds.token,
            refresh_token=creds.refresh_token,
            token_uri=creds.token_uri,
            client_id=creds.client_id,
            client_secret=creds.client_secret,
            scopes=creds.scopes,
            expiry=creds.expiry
        )
        
        # Save credentials
        await self.save_credentials(yt_creds)
        
        # Cache credentials
        self.credentials_cache[account_name] = creds
        
        logger.info(f"Authentication successful for {account_name} ({channel_info.get('channel_title')})")
        return yt_creds
    
    async def _get_channel_info(self, youtube) -> Dict[str, Any]:
        """Get channel information"""
        try:
            response = await asyncio.to_thread(
                youtube.channels().list,
                part="snippet,contentDetails,statistics",
                mine=True
            ).execute()
            
            if response.get("items"):
                channel = response["items"][0]
                return {
                    "channel_id": channel["id"],
                    "channel_title": channel["snippet"]["title"],
                    "email": None  # Email not available via API
                }
            
            return {}
        except Exception as e:
            logger.warning(f"Failed to get channel info: {e}")
            return {}
    
    async def load_credentials(self, account_name: str) -> Optional[YouTubeCredentials]:
        """
        Load credentials from storage
        
        Args:
            account_name: Account name
        
        Returns:
            YouTubeCredentials or None if not found
        
        Raises:
            FileNotFoundError: If credentials file not found
        """
        token_path = self._get_token_path(account_name)
        
        if not token_path.exists():
            raise FileNotFoundError(f"No credentials found for account: {account_name}")
        
        # Read encrypted token
        with open(token_path, "r") as f:
            encrypted_data = f.read()
        
        # Decrypt
        decrypted_data = self._decrypt(encrypted_data)
        
        # Parse JSON
        creds_dict = json.loads(decrypted_data)
        
        # Convert to model
        yt_creds = YouTubeCredentials(**creds_dict)
        
        # Check if refresh needed
        if self.config.auto_refresh:
            yt_creds = await self._auto_refresh(yt_creds)
        
        return yt_creds
    
    async def save_credentials(self, credentials: YouTubeCredentials):
        """Save credentials to storage"""
        token_path = self._get_token_path(credentials.account_name)
        
        # Convert to dict
        creds_dict = credentials.dict()
        
        # Serialize
        json_data = json.dumps(creds_dict, indent=2, default=str)
        
        # Encrypt
        encrypted_data = self._encrypt(json_data)
        
        # Save
        with open(token_path, "w") as f:
            f.write(encrypted_data)
        
        logger.info(f"Credentials saved for {credentials.account_name}")
    
    async def _auto_refresh(self, credentials: YouTubeCredentials) -> YouTubeCredentials:
        """Auto refresh token if needed"""
        if not credentials.expiry or not credentials.refresh_token:
            return credentials
        
        # Check if refresh needed
        threshold = timedelta(minutes=self.config.refresh_threshold_minutes)
        if datetime.utcnow() + threshold < credentials.expiry:
            return credentials
        
        logger.info(f"Token expiring soon, refreshing for {credentials.account_name}")
        return await self.refresh_token(credentials.account_name)
    
    async def refresh_token(self, account_name: str) -> YouTubeCredentials:
        """
        Refresh access token
        
        Args:
            account_name: Account name
        
        Returns:
            Updated YouTubeCredentials
        """
        # Load existing credentials
        yt_creds = await self.load_credentials(account_name)
        
        if not yt_creds.refresh_token:
            raise ValueError("No refresh token available, re-authentication required")
        
        # Create credentials object
        creds = Credentials(
            token=yt_creds.token,
            refresh_token=yt_creds.refresh_token,
            token_uri=yt_creds.token_uri,
            client_id=yt_creds.client_id,
            client_secret=yt_creds.client_secret,
            scopes=yt_creds.scopes
        )
        
        # Refresh
        await asyncio.to_thread(creds.refresh, Request())
        
        # Update credentials
        yt_creds.token = creds.token
        yt_creds.expiry = creds.expiry
        yt_creds.last_refreshed = datetime.utcnow()
        
        # Save updated credentials
        await self.save_credentials(yt_creds)
        
        # Update cache
        self.credentials_cache[account_name] = creds
        
        logger.info(f"Token refreshed for {account_name}")
        return yt_creds
    
    async def _validate_credentials(self, credentials: YouTubeCredentials) -> bool:
        """Validate credentials by making test API call"""
        try:
            youtube = await self.get_youtube_client_from_credentials(credentials)
            
            # Make test call
            await asyncio.to_thread(
                youtube.channels().list,
                part="snippet",
                mine=True
            ).execute()
            
            return True
        except Exception as e:
            logger.warning(f"Credential validation failed: {e}")
            return False
    
    async def get_youtube_client(self, account_name: str):
        """
        Get authenticated YouTube API client
        
        Args:
            account_name: Account name
        
        Returns:
            YouTube API client (googleapiclient.discovery.Resource)
        """
        # Check cache
        if account_name in self.credentials_cache:
            creds = self.credentials_cache[account_name]
        else:
            # Load credentials
            yt_creds = await self.load_credentials(account_name)
            
            # Convert to Credentials object
            creds = Credentials(
                token=yt_creds.token,
                refresh_token=yt_creds.refresh_token,
                token_uri=yt_creds.token_uri,
                client_id=yt_creds.client_id,
                client_secret=yt_creds.client_secret,
                scopes=yt_creds.scopes
            )
            
            # Cache
            self.credentials_cache[account_name] = creds
        
        # Build client
        youtube = build("youtube", "v3", credentials=creds)
        return youtube
    
    async def get_youtube_client_from_credentials(self, credentials: YouTubeCredentials):
        """Get YouTube API client from credentials object"""
        creds = Credentials(
            token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_uri=credentials.token_uri,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            scopes=credentials.scopes
        )
        
        return build("youtube", "v3", credentials=creds)
    
    async def get_auth_status(self, account_name: str) -> AuthStatus:
        """Get authentication status for account"""
        try:
            credentials = await self.load_credentials(account_name)
            
            if not credentials:
                return AuthStatus.NOT_AUTHENTICATED
            
            # Check expiry
            if credentials.expiry and credentials.expiry < datetime.utcnow():
                if credentials.refresh_token:
                    return AuthStatus.REFRESH_REQUIRED
                else:
                    return AuthStatus.TOKEN_EXPIRED
            
            # Validate
            if await self._validate_credentials(credentials):
                return AuthStatus.AUTHENTICATED
            else:
                return AuthStatus.INVALID_CREDENTIALS
        
        except FileNotFoundError:
            return AuthStatus.NOT_AUTHENTICATED
        except Exception as e:
            logger.error(f"Error checking auth status: {e}")
            return AuthStatus.ERROR
    
    async def list_accounts(self) -> List[str]:
        """List all authenticated accounts"""
        token_dir = Path(self.config.token_storage_path)
        
        if not token_dir.exists():
            return []
        
        accounts = []
        for token_file in token_dir.glob("*.json"):
            account_name = token_file.stem
            accounts.append(account_name)
        
        return accounts
    
    async def remove_account(self, account_name: str):
        """Remove account credentials"""
        token_path = self._get_token_path(account_name)
        
        if token_path.exists():
            token_path.unlink()
            logger.info(f"Removed credentials for {account_name}")
        
        # Remove from cache
        if account_name in self.credentials_cache:
            del self.credentials_cache[account_name]
    
    async def get_account_info(self, account_name: str) -> Optional[Dict[str, Any]]:
        """Get account information"""
        try:
            credentials = await self.load_credentials(account_name)
            
            if not credentials:
                return None
            
            status = await self.get_auth_status(account_name)
            
            return {
                "account_name": credentials.account_name,
                "channel_id": credentials.channel_id,
                "channel_title": credentials.channel_title,
                "email": credentials.email,
                "status": status.value,
                "expiry": credentials.expiry,
                "last_refreshed": credentials.last_refreshed,
                "created_at": credentials.created_at
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return None
