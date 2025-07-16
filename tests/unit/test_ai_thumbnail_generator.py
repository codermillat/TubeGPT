"""
Unit tests for ai_thumbnail_generator.py module.

Tests AI thumbnail generation with mocked APIs and validates
image creation, dimensions, and fallback functionality.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from PIL import Image
import io

# Import the module to test
from ai_thumbnail_generator import (
    AIThumbnailGenerator,
    generate_thumbnail_image,
    generate_thumbnails_for_ideas
)

class TestAIThumbnailGenerator:
    """Test suite for AIThumbnailGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create AIThumbnailGenerator instance for testing."""
        return AIThumbnailGenerator(api_backend='fallback')
    
    @pytest.fixture
    def generator_dalle(self):
        """Create AIThumbnailGenerator with DALL-E backend."""
        return AIThumbnailGenerator(api_backend='dall-e')
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def sample_ideas(self):
        """Sample video ideas with thumbnail texts."""
        return [
            {
                'title': 'Ultimate Cooking Guide',
                'thumbnail_texts': ['SECRET REVEALED', 'PERFECT RECIPE', 'CHEF TIPS']
            },
            {
                'title': 'Study Abroad Tips',
                'thumbnail_texts': ['HIDDEN SECRETS', 'STUDY TIPS', 'MUST KNOW']
            }
        ]
    
    def test_generator_initialization_fallback(self, generator):
        """Test generator initialization with fallback backend."""
        assert generator.api_backend == 'fallback'
        assert generator.thumbnail_size == (1280, 720)
        assert generator.display_size == (800, 450)
        assert 'professional' in generator.style_configs
        assert 'blue' in generator.color_schemes
    
    def test_generator_initialization_dalle(self, generator_dalle):
        """Test generator initialization with DALL-E backend."""
        assert generator_dalle.api_backend == 'dall-e'
        assert hasattr(generator_dalle, 'openai_api_key')
    
    def test_style_configs_structure(self, generator):
        """Test style configurations structure."""
        expected_styles = ['professional', 'fun', 'dramatic', 'educational']
        
        for style in expected_styles:
            assert style in generator.style_configs
            config = generator.style_configs[style]
            assert 'background_color' in config
            assert 'text_color' in config
            assert 'accent_color' in config
            assert 'prompt_style' in config
    
    def test_color_schemes_structure(self, generator):
        """Test color schemes structure."""
        expected_schemes = ['blue', 'red', 'green', 'purple', 'orange']
        
        for scheme in expected_schemes:
            assert scheme in generator.color_schemes
            colors = generator.color_schemes[scheme]
            assert 'primary' in colors
            assert 'secondary' in colors
            assert 'accent' in colors
    
    def test_generate_thumbnail_pil_fallback(self, generator, temp_output_dir):
        """Test thumbnail generation using PIL fallback."""
        output_path = temp_output_dir / "test_thumbnail.png"
        
        result_path = generator.generate_thumbnail_image(
            "SECRET REVEALED",
            {'tone': 'professional', 'color_scheme': 'blue'},
            str(output_path)
        )
        
        # Validate result
        assert result_path == str(output_path)
        assert output_path.exists()
        
        # Validate image properties
        with Image.open(output_path) as img:
            assert img.format == 'PNG'
            assert img.size == generator.thumbnail_size
    
    def test_generate_thumbnail_different_styles(self, generator, temp_output_dir):
        """Test thumbnail generation with different styles."""
        styles = [
            {'tone': 'professional', 'color_scheme': 'blue'},
            {'tone': 'fun', 'color_scheme': 'red'},
            {'tone': 'dramatic', 'color_scheme': 'purple'}
        ]
        
        for i, style in enumerate(styles):
            output_path = temp_output_dir / f"test_thumbnail_{i}.png"
            
            result_path = generator.generate_thumbnail_image(
                f"TEST TEXT {i}",
                style,
                str(output_path)
            )
            
            assert output_path.exists()
            
            # Validate image was created
            with Image.open(output_path) as img:
                assert img.size == generator.thumbnail_size
    
    def test_generate_thumbnail_empty_text(self, generator, temp_output_dir):
        """Test thumbnail generation with empty text."""
        output_path = temp_output_dir / "empty_text.png"
        
        with pytest.raises(ValueError, match="Thumbnail text cannot be empty"):
            generator.generate_thumbnail_image("", None, str(output_path))
    
    def test_generate_thumbnail_auto_path(self, generator):
        """Test thumbnail generation with automatic path generation."""
        result_path = generator.generate_thumbnail_image("AUTO PATH TEST")
        
        # Should generate path in thumbnails directory
        assert result_path.startswith(str(generator.THUMBNAILS_DIR) if hasattr(generator, 'THUMBNAILS_DIR') else 'thumbnails')
        assert result_path.endswith('.png')
        
        # Cleanup
        if os.path.exists(result_path):
            os.unlink(result_path)
    
    @patch('ai_thumbnail_generator.requests.get')
    @patch('ai_thumbnail_generator.openai.Image.create')
    def test_generate_with_dalle_success(self, mock_openai, mock_requests, generator_dalle, temp_output_dir):
        """Test successful DALL-E thumbnail generation."""
        # Setup mocks
        mock_openai.return_value = {
            'data': [{'url': 'https://example.com/image.png'}]
        }
        
        # Create a simple test image
        test_image = Image.new('RGB', (1024, 1024), color='blue')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        mock_response = Mock()
        mock_response.content = img_buffer.getvalue()
        mock_response.raise_for_status.return_value = None
        mock_requests.return_value = mock_response
        
        # Set API key for test
        generator_dalle.openai_api_key = 'test_key'
        
        output_path = temp_output_dir / "dalle_test.png"
        
        # Test generation
        with patch('ai_thumbnail_generator.openai.api_key', 'test_key'):
            result = generator_dalle._generate_with_dalle(
                "TEST TEXT",
                {'tone': 'professional'},
                output_path
            )
        
        assert result is True
        assert output_path.exists()
    
    @patch('ai_thumbnail_generator.requests.post')
    def test_generate_with_stable_diffusion_success(self, mock_post, generator, temp_output_dir):
        """Test successful Stable Diffusion thumbnail generation."""
        # Create a simple test image
        test_image = Image.new('RGB', (1024, 576), color='green')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        mock_response = Mock()
        mock_response.content = img_buffer.getvalue()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Set token for test
        generator.huggingface_token = 'test_token'
        
        output_path = temp_output_dir / "sd_test.png"
        
        result = generator._generate_with_stable_diffusion(
            "TEST TEXT",
            {'tone': 'professional'},
            output_path
        )
        
        assert result is True
        assert output_path.exists()
    
    def test_create_gradient_background(self, generator):
        """Test gradient background creation."""
        background = generator._create_gradient_background((400, 300), '#FF0000', '#0000FF')
        
        assert isinstance(background, Image.Image)
        assert background.size == (400, 300)
        assert background.mode == 'RGB'
    
    def test_add_text_overlay(self, generator):
        """Test text overlay addition."""
        # Create test background
        background = Image.new('RGB', (800, 600), color='blue')
        
        result = generator._add_text_overlay(
            background,
            "TEST TEXT",
            {'tone': 'professional'}
        )
        
        assert isinstance(result, Image.Image)
        assert result.size == background.size
    
    def test_generate_thumbnails_for_ideas(self, generator, sample_ideas, temp_output_dir):
        """Test batch thumbnail generation for ideas."""
        result = generator.generate_thumbnails_for_ideas(
            sample_ideas,
            {'tone': 'professional'},
            str(temp_output_dir)
        )
        
        # Validate results
        assert len(result) == len(sample_ideas)
        
        for i, idea in enumerate(result):
            assert 'thumbnail_image_path' in idea
            
            # Check if thumbnail was generated
            if idea['thumbnail_image_path']:
                assert os.path.exists(idea['thumbnail_image_path'])
                
                # Validate image
                with Image.open(idea['thumbnail_image_path']) as img:
                    assert img.format == 'PNG'
    
    def test_generate_thumbnails_missing_texts(self, generator, temp_output_dir):
        """Test thumbnail generation with missing thumbnail texts."""
        ideas_no_texts = [
            {'title': 'Test Video', 'thumbnail_texts': []},
            {'title': 'Another Video'}  # No thumbnail_texts key
        ]
        
        result = generator.generate_thumbnails_for_ideas(
            ideas_no_texts,
            {'tone': 'professional'},
            str(temp_output_dir)
        )
        
        # Should handle gracefully
        assert len(result) == 2
        for idea in result:
            assert 'thumbnail_image_path' in idea
            assert idea['thumbnail_image_path'] is None
    
    def test_generate_thumbnails_error_handling(self, generator, temp_output_dir):
        """Test error handling in batch generation."""
        # Create ideas with problematic text
        problematic_ideas = [
            {'title': 'Good Video', 'thumbnail_texts': ['GOOD TEXT']},
            {'title': 'Bad Video', 'thumbnail_texts': ['']}  # Empty text
        ]
        
        result = generator.generate_thumbnails_for_ideas(
            problematic_ideas,
            {'tone': 'professional'},
            str(temp_output_dir)
        )
        
        # Should handle errors gracefully
        assert len(result) == 2
        assert result[0]['thumbnail_image_path'] is not None  # Good one should work
        assert result[1]['thumbnail_image_path'] is None      # Bad one should fail gracefully


class TestUtilityFunctions:
    """Test utility functions."""
    
    @patch('ai_thumbnail_generator.AIThumbnailGenerator')
    def test_generate_thumbnail_image_utility(self, mock_generator_class):
        """Test generate_thumbnail_image utility function."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_thumbnail_image.return_value = '/path/to/thumbnail.png'
        
        result = generate_thumbnail_image("TEST TEXT", {'tone': 'fun'}, 'output.png')
        
        mock_generator_class.assert_called_once()
        mock_generator.generate_thumbnail_image.assert_called_once_with(
            "TEST TEXT", {'tone': 'fun'}, 'output.png'
        )
        assert result == '/path/to/thumbnail.png'
    
    @patch('ai_thumbnail_generator.AIThumbnailGenerator')
    def test_generate_thumbnails_for_ideas_utility(self, mock_generator_class):
        """Test generate_thumbnails_for_ideas utility function."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_thumbnails_for_ideas.return_value = [{'thumbnail_image_path': 'test.png'}]
        
        ideas = [{'title': 'test'}]
        style = {'tone': 'professional'}
        
        result = generate_thumbnails_for_ideas(ideas, style, 'output/')
        
        mock_generator_class.assert_called_once()
        mock_generator.generate_thumbnails_for_ideas.assert_called_once_with(
            ideas, style, 'output/'
        )
        assert result == [{'thumbnail_image_path': 'test.png'}]


class TestIntegration:
    """Integration tests for complete workflow."""
    
    def test_complete_thumbnail_workflow(self, temp_output_dir):
        """Test complete thumbnail generation workflow."""
        # Test data
        ideas = [
            {
                'title': 'Amazing Cooking Tips',
                'thumbnail_texts': ['AMAZING TIPS', 'COOKING SECRETS', 'MUST WATCH']
            }
        ]
        
        style = {
            'tone': 'fun',
            'color_scheme': 'orange'
        }
        
        # Run complete workflow
        generator = AIThumbnailGenerator(api_backend='fallback')
        result = generator.generate_thumbnails_for_ideas(ideas, style, str(temp_output_dir))
        
        # Validate complete result
        assert len(result) == 1
        idea = result[0]
        
        # Should have all original fields plus thumbnail path
        assert 'title' in idea
        assert 'thumbnail_texts' in idea
        assert 'thumbnail_image_path' in idea
        
        # Validate thumbnail was created
        if idea['thumbnail_image_path']:
            assert os.path.exists(idea['thumbnail_image_path'])
            
            # Validate image properties
            with Image.open(idea['thumbnail_image_path']) as img:
                assert img.format == 'PNG'
                assert img.size == generator.thumbnail_size


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])