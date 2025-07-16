"""
Unit tests for strategy_memory.py module.

Tests strategy persistence, validation, CRUD operations,
and error handling with comprehensive coverage.
"""

import pytest
import tempfile
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, Mock
from pydantic import ValidationError

# Import the module to test
from strategy_memory import (
    Strategy,
    StrategyMemory,
    save_strategy,
    load_strategy,
    list_strategies,
    delete_strategy,
    load_active_strategy,
    update_strategy
)

class TestStrategyModel:
    """Test suite for Strategy Pydantic model."""
    
    @pytest.fixture
    def valid_strategy_data(self):
        """Valid strategy data for testing."""
        return {
            'country': 'Bangladesh',
            'audience_type': 'university students',
            'audience_age_range': '18-25',
            'keywords': ['study tips', 'university life', 'student advice'],
            'goal': 'subscribers',
            'description': 'Content strategy for university students'
        }
    
    def test_strategy_creation_valid(self, valid_strategy_data):
        """Test successful strategy creation with valid data."""
        strategy = Strategy(**valid_strategy_data)
        
        assert strategy.country == 'Bangladesh'
        assert strategy.audience_type == 'university students'
        assert strategy.audience_age_range == '18-25'
        assert strategy.goal == 'subscribers'
        assert len(strategy.keywords) == 3
        assert strategy.strategy_id is not None
        assert isinstance(strategy.created_at, datetime)
        assert isinstance(strategy.updated_at, datetime)
    
    def test_strategy_auto_generated_fields(self, valid_strategy_data):
        """Test auto-generated fields like ID and timestamps."""
        strategy1 = Strategy(**valid_strategy_data)
        strategy2 = Strategy(**valid_strategy_data)
        
        # IDs should be unique
        assert strategy1.strategy_id != strategy2.strategy_id
        
        # Should have timestamps
        assert strategy1.created_at is not None
        assert strategy1.updated_at is not None
    
    def test_strategy_country_validation(self, valid_strategy_data):
        """Test country validation and normalization."""
        # Valid country
        valid_strategy_data['country'] = 'bangladesh'
        strategy = Strategy(**valid_strategy_data)
        assert strategy.country == 'Bangladesh'  # Should be title-cased
        
        # Empty country
        valid_strategy_data['country'] = ''
        with pytest.raises(ValidationError, match="Country cannot be empty"):
            Strategy(**valid_strategy_data)
        
        # Whitespace only
        valid_strategy_data['country'] = '   '
        with pytest.raises(ValidationError, match="Country cannot be empty"):
            Strategy(**valid_strategy_data)
    
    def test_strategy_audience_validation(self, valid_strategy_data):
        """Test audience type validation."""
        # Valid audience
        valid_strategy_data['audience_type'] = 'TECH PROFESSIONALS'
        strategy = Strategy(**valid_strategy_data)
        assert strategy.audience_type == 'tech professionals'  # Should be lowercase
        
        # Empty audience
        valid_strategy_data['audience_type'] = ''
        with pytest.raises(ValidationError, match="Audience type cannot be empty"):
            Strategy(**valid_strategy_data)
    
    def test_strategy_age_range_validation(self, valid_strategy_data):
        """Test age range validation."""
        # Valid age ranges
        valid_ranges = ['18-25', '25-35', '13-18', '35-65']
        for age_range in valid_ranges:
            valid_strategy_data['audience_age_range'] = age_range
            strategy = Strategy(**valid_strategy_data)
            assert strategy.audience_age_range == age_range
        
        # Invalid formats
        invalid_ranges = ['18', '18-', '-25', '25-18', '12-25', '18-101', 'eighteen-twentyfive']
        for age_range in invalid_ranges:
            valid_strategy_data['audience_age_range'] = age_range
            with pytest.raises(ValidationError):
                Strategy(**valid_strategy_data)
    
    def test_strategy_keywords_validation(self, valid_strategy_data):
        """Test keywords validation and cleaning."""
        # Valid keywords
        valid_strategy_data['keywords'] = ['keyword1', 'keyword2', 'keyword3']
        strategy = Strategy(**valid_strategy_data)
        assert len(strategy.keywords) == 3
        
        # Duplicate removal
        valid_strategy_data['keywords'] = ['keyword1', 'keyword1', 'keyword2']
        strategy = Strategy(**valid_strategy_data)
        assert len(strategy.keywords) == 2
        assert 'keyword1' in strategy.keywords
        assert 'keyword2' in strategy.keywords
        
        # Empty keywords should be filtered
        valid_strategy_data['keywords'] = ['keyword1', '', '   ', 'keyword2']
        strategy = Strategy(**valid_strategy_data)
        assert len(strategy.keywords) == 2
        
        # Too many keywords (should be limited to 20)
        valid_strategy_data['keywords'] = [f'keyword{i}' for i in range(25)]
        strategy = Strategy(**valid_strategy_data)
        assert len(strategy.keywords) == 20
    
    def test_strategy_goal_validation(self, valid_strategy_data):
        """Test goal validation."""
        # Valid goals
        valid_goals = ['views', 'subscribers', 'engagement', 'leads', 'sales']
        for goal in valid_goals:
            valid_strategy_data['goal'] = goal
            strategy = Strategy(**valid_strategy_data)
            assert strategy.goal == goal
        
        # Invalid goal
        valid_strategy_data['goal'] = 'invalid_goal'
        with pytest.raises(ValidationError, match="Goal must be one of"):
            Strategy(**valid_strategy_data)
    
    def test_strategy_description_validation(self, valid_strategy_data):
        """Test description validation."""
        # Valid description
        valid_strategy_data['description'] = 'This is a valid description'
        strategy = Strategy(**valid_strategy_data)
        assert strategy.description == 'This is a valid description'
        
        # Empty description should become None
        valid_strategy_data['description'] = ''
        strategy = Strategy(**valid_strategy_data)
        assert strategy.description is None
        
        # None description
        valid_strategy_data['description'] = None
        strategy = Strategy(**valid_strategy_data)
        assert strategy.description is None
    
    def test_strategy_update_timestamp(self, valid_strategy_data):
        """Test timestamp update functionality."""
        strategy = Strategy(**valid_strategy_data)
        original_time = strategy.updated_at
        
        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)
        
        strategy.update_timestamp()
        assert strategy.updated_at > original_time


class TestStrategyMemory:
    """Test suite for StrategyMemory class."""
    
    @pytest.fixture
    def temp_strategies_dir(self):
        """Create temporary strategies directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def strategy_memory(self, temp_strategies_dir):
        """Create StrategyMemory instance with temp directory."""
        return StrategyMemory(str(temp_strategies_dir))
    
    @pytest.fixture
    def valid_strategy_data(self):
        """Valid strategy data for testing."""
        return {
            'country': 'Bangladesh',
            'audience_type': 'university students',
            'audience_age_range': '18-25',
            'keywords': ['study tips', 'university life'],
            'goal': 'subscribers',
            'description': 'Test strategy'
        }
    
    def test_save_strategy_success(self, strategy_memory, valid_strategy_data):
        """Test successful strategy saving."""
        strategy_id = strategy_memory.save_strategy(valid_strategy_data)
        
        assert strategy_id is not None
        assert len(strategy_id) > 0
        
        # Check file was created
        file_path = strategy_memory.strategies_dir / f"{strategy_id}.json"
        assert file_path.exists()
        
        # Validate file content
        with open(file_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['country'] == 'Bangladesh'
        assert saved_data['goal'] == 'subscribers'
    
    def test_save_strategy_invalid_data(self, strategy_memory):
        """Test strategy saving with invalid data."""
        invalid_data = {
            'country': '',  # Invalid empty country
            'audience_type': 'students',
            'audience_age_range': '18-25',
            'goal': 'subscribers'
        }
        
        with pytest.raises(ValidationError):
            strategy_memory.save_strategy(invalid_data)
    
    def test_load_strategy_success(self, strategy_memory, valid_strategy_data):
        """Test successful strategy loading."""
        # Save first
        strategy_id = strategy_memory.save_strategy(valid_strategy_data)
        
        # Load
        loaded_strategy = strategy_memory.load_strategy(strategy_id)
        
        assert loaded_strategy['country'] == 'Bangladesh'
        assert loaded_strategy['goal'] == 'subscribers'
        assert loaded_strategy['strategy_id'] == strategy_id
    
    def test_load_strategy_not_found(self, strategy_memory):
        """Test loading non-existent strategy."""
        fake_id = str(uuid.uuid4())
        
        with pytest.raises(FileNotFoundError, match="Strategy not found"):
            strategy_memory.load_strategy(fake_id)
    
    def test_load_strategy_corrupted_data(self, strategy_memory, temp_strategies_dir):
        """Test loading corrupted strategy file."""
        # Create corrupted JSON file
        fake_id = str(uuid.uuid4())
        file_path = temp_strategies_dir / f"{fake_id}.json"
        
        with open(file_path, 'w') as f:
            f.write('{"invalid": json}')  # Invalid JSON
        
        with pytest.raises(ValueError, match="Strategy data is corrupted"):
            strategy_memory.load_strategy(fake_id)
    
    def test_list_strategies(self, strategy_memory, valid_strategy_data):
        """Test listing all strategies."""
        # Initially empty
        strategies = strategy_memory.list_strategies()
        assert len(strategies) == 0
        
        # Save some strategies
        id1 = strategy_memory.save_strategy(valid_strategy_data)
        
        valid_strategy_data['goal'] = 'views'
        id2 = strategy_memory.save_strategy(valid_strategy_data)
        
        # List strategies
        strategies = strategy_memory.list_strategies()
        assert len(strategies) == 2
        
        # Check structure
        for strategy in strategies:
            assert 'strategy_id' in strategy
            assert 'country' in strategy
            assert 'audience_type' in strategy
            assert 'goal' in strategy
            assert 'created_at' in strategy
            assert 'updated_at' in strategy
        
        # Should be sorted by updated_at (most recent first)
        strategy_ids = [s['strategy_id'] for s in strategies]
        assert id2 in strategy_ids  # More recent should be in list
        assert id1 in strategy_ids
    
    def test_delete_strategy_success(self, strategy_memory, valid_strategy_data):
        """Test successful strategy deletion."""
        # Save strategy
        strategy_id = strategy_memory.save_strategy(valid_strategy_data)
        
        # Verify it exists
        file_path = strategy_memory.strategies_dir / f"{strategy_id}.json"
        assert file_path.exists()
        
        # Delete
        result = strategy_memory.delete_strategy(strategy_id)
        assert result is True
        
        # Verify file is gone
        assert not file_path.exists()
    
    def test_delete_strategy_not_found(self, strategy_memory):
        """Test deleting non-existent strategy."""
        fake_id = str(uuid.uuid4())
        result = strategy_memory.delete_strategy(fake_id)
        assert result is False
    
    def test_update_strategy(self, strategy_memory, valid_strategy_data):
        """Test strategy updating."""
        # Save strategy
        strategy_id = strategy_memory.save_strategy(valid_strategy_data)
        
        # Update
        updates = {
            'goal': 'views',
            'description': 'Updated description'
        }
        
        updated_strategy = strategy_memory.update_strategy(strategy_id, updates)
        
        assert updated_strategy['goal'] == 'views'
        assert updated_strategy['description'] == 'Updated description'
        assert updated_strategy['country'] == 'Bangladesh'  # Unchanged field
    
    def test_load_active_strategy(self, strategy_memory, valid_strategy_data):
        """Test loading active (most recent) strategy."""
        # No strategies initially
        active = strategy_memory.load_active_strategy()
        assert active is None
        
        # Save first strategy
        id1 = strategy_memory.save_strategy(valid_strategy_data)
        
        active = strategy_memory.load_active_strategy()
        assert active['strategy_id'] == id1
        
        # Save second strategy (should become active)
        import time
        time.sleep(0.01)  # Ensure different timestamp
        
        valid_strategy_data['goal'] = 'views'
        id2 = strategy_memory.save_strategy(valid_strategy_data)
        
        active = strategy_memory.load_active_strategy()
        assert active['strategy_id'] == id2  # More recent
    
    def test_search_strategies(self, strategy_memory, valid_strategy_data):
        """Test strategy search functionality."""
        # Save test strategies
        strategy1 = valid_strategy_data.copy()
        strategy1['goal'] = 'subscribers'
        strategy1['country'] = 'Bangladesh'
        strategy1['description'] = 'University students content'
        id1 = strategy_memory.save_strategy(strategy1)
        
        strategy2 = valid_strategy_data.copy()
        strategy2['goal'] = 'views'
        strategy2['country'] = 'India'
        strategy2['description'] = 'Tech professionals content'
        id2 = strategy_memory.save_strategy(strategy2)
        
        # Search by goal
        results = strategy_memory.search_strategies(goal='subscribers')
        assert len(results) == 1
        assert results[0]['strategy_id'] == id1
        
        # Search by country
        results = strategy_memory.search_strategies(country='India')
        assert len(results) == 1
        assert results[0]['strategy_id'] == id2
        
        # Search by query
        results = strategy_memory.search_strategies(query='university')
        assert len(results) == 1
        assert results[0]['strategy_id'] == id1
        
        # Combined search
        results = strategy_memory.search_strategies(goal='views', country='India')
        assert len(results) == 1
        assert results[0]['strategy_id'] == id2


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.fixture
    def temp_strategies_dir(self):
        """Create temporary strategies directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def valid_strategy_data(self):
        """Valid strategy data for testing."""
        return {
            'country': 'Bangladesh',
            'audience_type': 'students',
            'audience_age_range': '18-25',
            'keywords': ['study', 'tips'],
            'goal': 'subscribers'
        }
    
    @patch('strategy_memory.strategy_memory')
    def test_save_strategy_convenience(self, mock_memory, valid_strategy_data):
        """Test save_strategy convenience function."""
        mock_memory.save_strategy.return_value = 'test_id'
        
        result = save_strategy(valid_strategy_data)
        
        mock_memory.save_strategy.assert_called_once_with(valid_strategy_data)
        assert result == 'test_id'
    
    @patch('strategy_memory.strategy_memory')
    def test_load_strategy_convenience(self, mock_memory):
        """Test load_strategy convenience function."""
        mock_memory.load_strategy.return_value = {'strategy_id': 'test_id'}
        
        result = load_strategy('test_id')
        
        mock_memory.load_strategy.assert_called_once_with('test_id')
        assert result == {'strategy_id': 'test_id'}
    
    @patch('strategy_memory.strategy_memory')
    def test_list_strategies_convenience(self, mock_memory):
        """Test list_strategies convenience function."""
        mock_memory.list_strategies.return_value = [{'strategy_id': 'test_id'}]
        
        result = list_strategies()
        
        mock_memory.list_strategies.assert_called_once()
        assert result == [{'strategy_id': 'test_id'}]
    
    @patch('strategy_memory.strategy_memory')
    def test_delete_strategy_convenience(self, mock_memory):
        """Test delete_strategy convenience function."""
        mock_memory.delete_strategy.return_value = True
        
        result = delete_strategy('test_id')
        
        mock_memory.delete_strategy.assert_called_once_with('test_id')
        assert result is True
    
    @patch('strategy_memory.strategy_memory')
    def test_load_active_strategy_convenience(self, mock_memory):
        """Test load_active_strategy convenience function."""
        mock_memory.load_active_strategy.return_value = {'strategy_id': 'active_id'}
        
        result = load_active_strategy()
        
        mock_memory.load_active_strategy.assert_called_once()
        assert result == {'strategy_id': 'active_id'}


class TestIntegration:
    """Integration tests for complete workflow."""
    
    def test_complete_strategy_workflow(self):
        """Test complete strategy management workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory = StrategyMemory(temp_dir)
            
            # Create strategy
            strategy_data = {
                'country': 'Bangladesh',
                'audience_type': 'university students',
                'audience_age_range': '18-25',
                'keywords': ['study tips', 'university life', 'academic success'],
                'goal': 'subscribers',
                'description': 'Content strategy for university students in Bangladesh'
            }
            
            # Save
            strategy_id = memory.save_strategy(strategy_data)
            assert strategy_id is not None
            
            # Load
            loaded = memory.load_strategy(strategy_id)
            assert loaded['country'] == 'Bangladesh'
            assert loaded['goal'] == 'subscribers'
            
            # Update
            updated = memory.update_strategy(strategy_id, {'goal': 'views'})
            assert updated['goal'] == 'views'
            assert updated['country'] == 'Bangladesh'  # Unchanged
            
            # List
            all_strategies = memory.list_strategies()
            assert len(all_strategies) == 1
            assert all_strategies[0]['strategy_id'] == strategy_id
            
            # Active
            active = memory.load_active_strategy()
            assert active['strategy_id'] == strategy_id
            
            # Search
            results = memory.search_strategies(goal='views')
            assert len(results) == 1
            
            # Delete
            deleted = memory.delete_strategy(strategy_id)
            assert deleted is True
            
            # Verify deletion
            final_list = memory.list_strategies()
            assert len(final_list) == 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])