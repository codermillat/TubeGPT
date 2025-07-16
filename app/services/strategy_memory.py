"""
Strategy Memory Module for YouTube Content Strategy Management.

This module provides persistent storage and management for user content strategies
with validation, error handling, and easy integration with the analysis pipeline.

Features:
1. Pydantic-based strategy validation and schema
2. JSON file-based persistence with auto-folder creation
3. CRUD operations with comprehensive error handling
4. Active strategy management for seamless workflow
5. CLI and API integration support
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator, ValidationError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create strategies directory
STRATEGIES_DIR = Path("strategies")
STRATEGIES_DIR.mkdir(exist_ok=True)

class Strategy(BaseModel):
    """
    Pydantic model for YouTube content strategy validation and serialization.
    
    Defines the complete schema for content strategies including audience,
    goals, keywords, and metadata with comprehensive validation.
    """
    
    strategy_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    country: str = Field(..., min_length=2, max_length=50)
    audience_type: str = Field(..., min_length=3, max_length=100)
    audience_age_range: str = Field(..., regex=r'^\d{1,2}-\d{1,2}$')
    keywords: List[str] = Field(default_factory=list, max_items=20)
    goal: str = Field(..., regex=r'^(views|subscribers|engagement|leads|sales)$')
    description: Optional[str] = Field(None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('country')
    def validate_country(cls, v):
        """Validate and normalize country name."""
        v = v.strip().title()
        if not v:
            raise ValueError('Country cannot be empty')
        return v
    
    @validator('audience_type')
    def validate_audience_type(cls, v):
        """Validate and normalize audience type."""
        v = v.strip().lower()
        if not v:
            raise ValueError('Audience type cannot be empty')
        return v
    
    @validator('audience_age_range')
    def validate_age_range(cls, v):
        """Validate age range format and logic."""
        if not v:
            raise ValueError('Age range cannot be empty')
        
        try:
            start, end = map(int, v.split('-'))
            if start >= end:
                raise ValueError('Start age must be less than end age')
            if start < 13 or end > 100:
                raise ValueError('Age range must be between 13-100')
            return v
        except ValueError as e:
            if 'invalid literal' in str(e):
                raise ValueError('Age range must be in format "18-35"')
            raise
    
    @validator('keywords')
    def validate_keywords(cls, v):
        """Validate and clean keywords list."""
        if not isinstance(v, list):
            raise ValueError('Keywords must be a list')
        
        # Clean and deduplicate keywords
        cleaned = []
        for keyword in v:
            if isinstance(keyword, str):
                keyword = keyword.strip().lower()
                if keyword and keyword not in cleaned:
                    cleaned.append(keyword)
        
        return cleaned[:20]  # Limit to 20 keywords
    
    @validator('goal')
    def validate_goal(cls, v):
        """Validate goal value."""
        v = v.strip().lower()
        valid_goals = ['views', 'subscribers', 'engagement', 'leads', 'sales']
        if v not in valid_goals:
            raise ValueError(f'Goal must be one of: {", ".join(valid_goals)}')
        return v
    
    @validator('description')
    def validate_description(cls, v):
        """Validate and clean description."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class StrategyMemory:
    """
    Strategy memory manager for persistent storage and retrieval.
    
    Handles CRUD operations for content strategies with JSON file persistence,
    validation, error handling, and active strategy management.
    """
    
    def __init__(self, strategies_dir: str = None):
        """
        Initialize strategy memory manager.
        
        Args:
            strategies_dir (str, optional): Custom strategies directory path
        """
        self.strategies_dir = Path(strategies_dir) if strategies_dir else STRATEGIES_DIR
        self.strategies_dir.mkdir(exist_ok=True)
        
        logger.info(f"Strategy memory initialized with directory: {self.strategies_dir}")
    
    def save_strategy(self, data: Dict[str, Any]) -> str:
        """
        Save a strategy to persistent storage.
        
        Args:
            data (dict): Strategy data dictionary
            
        Returns:
            str: Strategy ID of saved strategy
            
        Raises:
            ValidationError: If strategy data is invalid
            IOError: If file cannot be written
        """
        try:
            logger.info("Saving new strategy")
            
            # Validate and create strategy object
            strategy = Strategy(**data)
            strategy_id = strategy.strategy_id
            
            # Save to JSON file
            file_path = self.strategies_dir / f"{strategy_id}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(strategy.dict(), f, indent=2, default=str, ensure_ascii=False)
            
            logger.info(f"Strategy saved successfully: {strategy_id}")
            return strategy_id
            
        except ValidationError as e:
            logger.error(f"Strategy validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saving strategy: {e}")
            raise IOError(f"Failed to save strategy: {str(e)}")
    
    def load_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """
        Load a strategy from persistent storage.
        
        Args:
            strategy_id (str): Strategy ID to load
            
        Returns:
            dict: Strategy data dictionary
            
        Raises:
            FileNotFoundError: If strategy doesn't exist
            ValueError: If strategy data is corrupted
        """
        try:
            logger.info(f"Loading strategy: {strategy_id}")
            
            file_path = self.strategies_dir / f"{strategy_id}.json"
            
            if not file_path.exists():
                raise FileNotFoundError(f"Strategy not found: {strategy_id}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate loaded data
            strategy = Strategy(**data)
            
            logger.info(f"Strategy loaded successfully: {strategy_id}")
            return strategy.dict()
            
        except FileNotFoundError:
            logger.error(f"Strategy not found: {strategy_id}")
            raise
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Strategy data corrupted for {strategy_id}: {e}")
            raise ValueError(f"Strategy data is corrupted: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading strategy {strategy_id}: {e}")
            raise IOError(f"Failed to load strategy: {str(e)}")
    
    def list_strategies(self) -> List[Dict[str, Any]]:
        """
        List all saved strategies with metadata.
        
        Returns:
            List[dict]: List of strategy summaries with basic info
        """
        try:
            logger.info("Listing all strategies")
            
            strategies = []
            
            for file_path in self.strategies_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Create summary with essential info
                    summary = {
                        'strategy_id': data.get('strategy_id'),
                        'country': data.get('country'),
                        'audience_type': data.get('audience_type'),
                        'goal': data.get('goal'),
                        'keywords_count': len(data.get('keywords', [])),
                        'created_at': data.get('created_at'),
                        'updated_at': data.get('updated_at'),
                        'description': data.get('description', '')[:100] + '...' if data.get('description', '') else None
                    }
                    
                    strategies.append(summary)
                    
                except Exception as e:
                    logger.warning(f"Skipping corrupted strategy file {file_path}: {e}")
                    continue
            
            # Sort by updated_at (most recent first)
            strategies.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            
            logger.info(f"Found {len(strategies)} strategies")
            return strategies
            
        except Exception as e:
            logger.error(f"Error listing strategies: {e}")
            return []
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """
        Delete a strategy from persistent storage.
        
        Args:
            strategy_id (str): Strategy ID to delete
            
        Returns:
            bool: True if deleted successfully, False if not found
            
        Raises:
            IOError: If file cannot be deleted
        """
        try:
            logger.info(f"Deleting strategy: {strategy_id}")
            
            file_path = self.strategies_dir / f"{strategy_id}.json"
            
            if not file_path.exists():
                logger.warning(f"Strategy not found for deletion: {strategy_id}")
                return False
            
            file_path.unlink()
            
            logger.info(f"Strategy deleted successfully: {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting strategy {strategy_id}: {e}")
            raise IOError(f"Failed to delete strategy: {str(e)}")
    
    def update_strategy(self, strategy_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing strategy.
        
        Args:
            strategy_id (str): Strategy ID to update
            updates (dict): Fields to update
            
        Returns:
            dict: Updated strategy data
            
        Raises:
            FileNotFoundError: If strategy doesn't exist
            ValidationError: If updated data is invalid
        """
        try:
            logger.info(f"Updating strategy: {strategy_id}")
            
            # Load existing strategy
            existing_data = self.load_strategy(strategy_id)
            
            # Apply updates
            existing_data.update(updates)
            existing_data['updated_at'] = datetime.now().isoformat()
            
            # Validate updated data
            strategy = Strategy(**existing_data)
            
            # Save updated strategy
            file_path = self.strategies_dir / f"{strategy_id}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(strategy.dict(), f, indent=2, default=str, ensure_ascii=False)
            
            logger.info(f"Strategy updated successfully: {strategy_id}")
            return strategy.dict()
            
        except Exception as e:
            logger.error(f"Error updating strategy {strategy_id}: {e}")
            raise
    
    def load_active_strategy(self) -> Optional[Dict[str, Any]]:
        """
        Load the most recently updated strategy as the active strategy.
        
        Returns:
            dict or None: Most recent strategy data, or None if no strategies exist
        """
        try:
            logger.info("Loading active (most recent) strategy")
            
            strategies = self.list_strategies()
            
            if not strategies:
                logger.info("No strategies found")
                return None
            
            # Get the most recent strategy (first in sorted list)
            most_recent = strategies[0]
            strategy_id = most_recent['strategy_id']
            
            active_strategy = self.load_strategy(strategy_id)
            
            logger.info(f"Active strategy loaded: {strategy_id}")
            return active_strategy
            
        except Exception as e:
            logger.error(f"Error loading active strategy: {e}")
            return None
    
    def search_strategies(self, query: str = None, goal: str = None, 
                         country: str = None) -> List[Dict[str, Any]]:
        """
        Search strategies by various criteria.
        
        Args:
            query (str, optional): Text search in description and audience_type
            goal (str, optional): Filter by goal
            country (str, optional): Filter by country
            
        Returns:
            List[dict]: Filtered list of strategy summaries
        """
        try:
            logger.info(f"Searching strategies with query='{query}', goal='{goal}', country='{country}'")
            
            all_strategies = self.list_strategies()
            filtered = []
            
            for strategy in all_strategies:
                # Apply filters
                if goal and strategy.get('goal', '').lower() != goal.lower():
                    continue
                
                if country and strategy.get('country', '').lower() != country.lower():
                    continue
                
                if query:
                    query_lower = query.lower()
                    searchable_text = f"{strategy.get('audience_type', '')} {strategy.get('description', '')}".lower()
                    if query_lower not in searchable_text:
                        continue
                
                filtered.append(strategy)
            
            logger.info(f"Found {len(filtered)} strategies matching criteria")
            return filtered
            
        except Exception as e:
            logger.error(f"Error searching strategies: {e}")
            return []

# Global instance for easy import
strategy_memory = StrategyMemory()

# Convenience functions for easy integration
def save_strategy(data: Dict[str, Any]) -> str:
    """
    Convenience function to save a strategy.
    
    Args:
        data (dict): Strategy data
        
    Returns:
        str: Strategy ID
    """
    return strategy_memory.save_strategy(data)

def load_strategy(strategy_id: str) -> Dict[str, Any]:
    """
    Convenience function to load a strategy.
    
    Args:
        strategy_id (str): Strategy ID
        
    Returns:
        dict: Strategy data
    """
    return strategy_memory.load_strategy(strategy_id)

def list_strategies() -> List[Dict[str, Any]]:
    """
    Convenience function to list all strategies.
    
    Returns:
        List[dict]: Strategy summaries
    """
    return strategy_memory.list_strategies()

def delete_strategy(strategy_id: str) -> bool:
    """
    Convenience function to delete a strategy.
    
    Args:
        strategy_id (str): Strategy ID
        
    Returns:
        bool: Success status
    """
    return strategy_memory.delete_strategy(strategy_id)

def load_active_strategy() -> Optional[Dict[str, Any]]:
    """
    Convenience function to load the active strategy.
    
    Returns:
        dict or None: Active strategy data
    """
    return strategy_memory.load_active_strategy()

def update_strategy(strategy_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to update a strategy.
    
    Args:
        strategy_id (str): Strategy ID
        updates (dict): Updates to apply
        
    Returns:
        dict: Updated strategy data
    """
    return strategy_memory.update_strategy(strategy_id, updates)

def main():
    """
    Example usage of the strategy memory system.
    """
    try:
        print("Strategy Memory System Example")
        print("=" * 40)
        
        # Example strategy data
        sample_strategy = {
            'country': 'Bangladesh',
            'audience_type': 'university students',
            'audience_age_range': '18-25',
            'keywords': ['study tips', 'university life', 'student advice', 'academic success'],
            'goal': 'subscribers',
            'description': 'Content strategy focused on helping university students succeed academically and socially.'
        }
        
        # Save strategy
        strategy_id = save_strategy(sample_strategy)
        print(f"✅ Strategy saved with ID: {strategy_id}")
        
        # Load strategy
        loaded_strategy = load_strategy(strategy_id)
        print(f"✅ Strategy loaded: {loaded_strategy['audience_type']} in {loaded_strategy['country']}")
        
        # List all strategies
        all_strategies = list_strategies()
        print(f"✅ Found {len(all_strategies)} total strategies")
        
        # Load active strategy
        active = load_active_strategy()
        if active:
            print(f"✅ Active strategy: {active['goal']} goal for {active['audience_type']}")
        
        # Update strategy
        updates = {'description': 'Updated description with more focus on practical tips'}
        updated = update_strategy(strategy_id, updates)
        print(f"✅ Strategy updated: {updated['updated_at']}")
        
        # Search strategies
        search_results = strategy_memory.search_strategies(goal='subscribers')
        print(f"✅ Found {len(search_results)} strategies with 'subscribers' goal")
        
        print(f"\nStrategies saved in: {STRATEGIES_DIR}")
        
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Main execution error: {e}")

if __name__ == "__main__":
    main()