"""
Tron blockchain integration utilities.
Handles USDT TRC20 deposits, withdrawals, and balance monitoring.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
import time

from tronpy import Tron
from tronpy.exceptions import TransactionError, ApiError, ValidationError
from tronpy.keys import PrivateKey

from ..core.config import settings

# Setup logging
logger = logging.getLogger(__name__)

# USDT TRC20 contract address on Tron mainnet
USDT_CONTRACT_ADDRESS = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"

# Minimum confirmations required for deposits
MIN_CONFIRMATIONS = 12


class TronService:
    """Service for Tron blockchain operations."""
    
    def __init__(self):
        """Initialize Tron service with network configuration."""
        if settings.tron_network == "mainnet":
            self.client = Tron()
        else:
            # For testnet (Shasta)
            self.client = Tron(network='shasta')
        
        # Setup USDT contract
        if settings.tron_network == "mainnet":
            self.usdt_contract = self.client.get_contract(USDT_CONTRACT_ADDRESS)
        else:
            # For testnet, you need to deploy or use a test USDT contract
            # This is a placeholder - replace with actual testnet contract
            self.usdt_contract = None
        
        # Company wallet setup
        if settings.company_wallet_private_key:
            try:
                self.company_wallet = PrivateKey(bytes.fromhex(settings.company_wallet_private_key))
                self.company_address = self.company_wallet.public_key.to_base58check_address()
                logger.info(f"Company wallet initialized: {self.company_address}")
            except Exception as e:
                logger.error(f"Failed to initialize company wallet: {e}")
                self.company_wallet = None
                self.company_address = settings.company_wallet_address
        else:
            self.company_wallet = None
            self.company_address = settings.company_wallet_address
    
    def get_account_balance(self, address: str) -> Dict[str, Decimal]:
        """
        Get TRX and USDT balance for an address.
        
        Args:
            address: Tron wallet address
            
        Returns:
            Dict containing TRX and USDT balances
        """
        try:
            # Get TRX balance
            trx_balance = self.client.get_account_balance(address)
            trx_balance_decimal = Decimal(str(trx_balance)) / Decimal('1000000')  # TRX has 6 decimals
            
            # Get USDT balance
            usdt_balance_decimal = Decimal('0')
            if self.usdt_contract:
                try:
                    usdt_balance = self.usdt_contract.functions.balanceOf(address)
                    usdt_balance_decimal = Decimal(str(usdt_balance)) / Decimal('1000000')  # USDT has 6 decimals
                except Exception as e:
                    logger.warning(f"Failed to get USDT balance for {address}: {e}")
            
            return {
                "TRX": trx_balance_decimal,
                "USDT": usdt_balance_decimal
            }
            
        except Exception as e:
            logger.error(f"Failed to get balance for {address}: {e}")
            return {"TRX": Decimal('0'), "USDT": Decimal('0')}
    
    def send_usdt(
        self, 
        to_address: str, 
        amount: Decimal, 
        memo: Optional[str] = None
    ) -> Optional[str]:
        """
        Send USDT to specified address.
        
        Args:
            to_address: Destination Tron address
            amount: Amount of USDT to send
            memo: Optional transaction memo
            
        Returns:
            Transaction hash if successful, None otherwise
        """
        if not self.company_wallet or not self.usdt_contract:
            logger.error("Company wallet or USDT contract not initialized")
            return None
        
        try:
            # Convert amount to contract units (6 decimals for USDT)
            amount_units = int(amount * Decimal('1000000'))
            
            # Build transaction
            txn = (
                self.usdt_contract.functions.transfer(to_address, amount_units)
                .with_owner(self.company_address)
                .fee_limit(100_000_000)  # 100 TRX fee limit
            )
            
            # Sign and broadcast transaction
            txn = txn.build().sign(self.company_wallet)
            result = txn.broadcast()
            
            if result and 'txid' in result:
                tx_hash = result['txid']
                logger.info(f"USDT transfer successful: {tx_hash}")
                return tx_hash
            else:
                logger.error(f"USDT transfer failed: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to send USDT: {e}")
            return None
    
    def get_usdt_transactions(
        self, 
        address: str, 
        limit: int = 50,
        start_timestamp: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get USDT transactions for an address.
        
        Args:
            address: Tron wallet address
            limit: Maximum number of transactions to fetch
            start_timestamp: Start timestamp for filtering (Unix timestamp in milliseconds)
            
        Returns:
            List of transaction dictionaries
        """
        if not self.usdt_contract:
            logger.warning("USDT contract not initialized")
            return []
        
        try:
            # Get TRC20 transfers for USDT contract
            # This is a simplified implementation - in production you might want to use
            # TronGrid API or TronScan API for more detailed transaction history
            
            transactions = []
            
            # Note: tronpy doesn't have built-in TRC20 transaction history
            # You would typically use TronGrid API for this:
            # GET https://api.trongrid.io/v1/accounts/{address}/transactions/trc20
            
            # For now, return empty list - implement with TronGrid API in production
            logger.info(f"Fetching USDT transactions for {address} (limit: {limit})")
            
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get USDT transactions for {address}: {e}")
            return []
    
    def check_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Check transaction status and confirmations.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Dictionary with transaction status information
        """
        try:
            # Get transaction info
            tx_info = self.client.get_transaction(tx_hash)
            
            if not tx_info:
                return {
                    "exists": False,
                    "confirmed": False,
                    "confirmations": 0,
                    "success": False
                }
            
            # Check if transaction is confirmed
            current_block = self.client.get_latest_block_number()
            tx_block = tx_info.get('blockNumber', 0)
            
            confirmations = current_block - tx_block if tx_block > 0 else 0
            is_confirmed = confirmations >= MIN_CONFIRMATIONS
            
            # Check transaction result
            is_success = tx_info.get('receipt', {}).get('result') == 'SUCCESS'
            
            return {
                "exists": True,
                "confirmed": is_confirmed,
                "confirmations": confirmations,
                "success": is_success,
                "block_number": tx_block,
                "timestamp": tx_info.get('blockTimeStamp', 0),
                "energy_used": tx_info.get('receipt', {}).get('energy_used', 0),
                "net_used": tx_info.get('receipt', {}).get('net_used', 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to check transaction status for {tx_hash}: {e}")
            return {
                "exists": False,
                "confirmed": False,
                "confirmations": 0,
                "success": False,
                "error": str(e)
            }
    
    def generate_address(self) -> Dict[str, str]:
        """
        Generate a new Tron address and private key.
        
        Returns:
            Dictionary with address and private key
        """
        try:
            # Generate new private key
            private_key = PrivateKey.random()
            address = private_key.public_key.to_base58check_address()
            
            return {
                "address": address,
                "private_key": private_key.hex()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate address: {e}")
            return {"address": "", "private_key": ""}
    
    def is_valid_address(self, address: str) -> bool:
        """
        Validate Tron address format.
        
        Args:
            address: Tron address to validate
            
        Returns:
            True if address is valid, False otherwise
        """
        try:
            # Basic validation - Tron addresses start with 'T' and are 34 characters
            if not address.startswith('T') or len(address) != 34:
                return False
            
            # Try to decode the address
            from tronpy.keys import to_hex_address
            to_hex_address(address)
            return True
            
        except Exception:
            return False
    
    async def monitor_deposits(
        self, 
        callback_func,
        check_interval: int = 30
    ) -> None:
        """
        Monitor for incoming USDT deposits to company wallet.
        
        Args:
            callback_func: Function to call when deposits are found
            check_interval: Check interval in seconds
        """
        logger.info(f"Starting deposit monitoring for {self.company_address}")
        
        last_check_time = int(time.time() * 1000)  # Convert to milliseconds
        
        while True:
            try:
                # Get recent USDT transactions
                transactions = self.get_usdt_transactions(
                    self.company_address,
                    limit=50,
                    start_timestamp=last_check_time
                )
                
                # Process new deposits
                for tx in transactions:
                    if (tx.get('to') == self.company_address and 
                        tx.get('timestamp', 0) > last_check_time):
                        
                        # Call callback function for each deposit
                        await callback_func(tx)
                
                last_check_time = int(time.time() * 1000)
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in deposit monitoring: {e}")
                await asyncio.sleep(check_interval)


# Global Tron service instance (지연 초기화)
tron_service = None

def get_tron_service():
    """Tron 서비스 인스턴스를 반환합니다 (지연 초기화)."""
    global tron_service
    if tron_service is None:
        tron_service = TronService()
    return tron_service
