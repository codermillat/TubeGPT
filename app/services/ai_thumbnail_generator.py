"""
AI Thumbnail Generator Module for YouTube Content Creation.

This module generates professional YouTube thumbnails with overlay text using
multiple AI backends (DALL-E, Stable Diffusion) with PIL fallback for reliability.

Features:
1. Multiple AI backend support (DALL-E, Stable Diffusion, Canva API)
2. Professional thumbnail composition with text overlays
3. Configurable styles and color schemes
4. PIL fallback for offline generation
5. Batch processing for multiple video ideas
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create thumbnails directory
THUMBNAILS_DIR = Path("thumbnails")
THUMBNAILS_DIR.mkdir(exist_ok=True)

class AIThumbnailGenerator:
    """
    Generates AI-powered YouTube thumbnails with text overlays.
    
    Supports multiple backends (DALL-E, Stable Diffusion) with PIL fallback
    for reliable thumbnail generation with professional styling.
    """
    
    def __init__(self, api_backend: str = None):
        """
        Initialize the AI Thumbnail Generator.
        
        Args:
            api_backend (str): Backend to use ('dall-e', 'stable-diffusion', 'fallback')
        """
        self.api_backend = api_backend or os.getenv('THUMBNAIL_API', 'fallback')
        
        # API keys
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.huggingface_token = os.getenv('HUGGINGFACE_TOKEN')
        
        # Thumbnail specifications
        self.thumbnail_size = (1280, 720)  # YouTube recommended size
        self.display_size = (800, 450)     # Display size for web
        
        # Style configurations
        self.style_configs = {
            'professional': {
                'background_color': '#2C3E50',
                'text_color': '#FFFFFF',
                'accent_color': '#3498DB',
                'font_weight': 'bold',
                'prompt_style': 'clean, professional, minimalist'
            },
            'fun': {
                'background_color': '#E74C3C',
                'text_color': '#FFFFFF',
                'accent_color': '#F39C12',
                'font_weight': 'bold',
                'prompt_style': 'colorful, energetic, playful'
            },
            'dramatic': {
                'background_color': '#1A1A1A',
                'text_color': '#FFFFFF',
                'accent_color': '#E74C3C',
                'font_weight': 'bold',
                'prompt_style': 'dark, cinematic, high contrast'
            },
            'educational': {
                'background_color': '#34495E',
                'text_color': '#FFFFFF',
                'accent_color': '#2ECC71',
                'font_weight': 'bold',
                'prompt_style': 'clean, academic, trustworthy'
            }
        }
        
        # Color schemes
        self.color_schemes = {
            'blue': {'primary': '#3498DB', 'secondary': '#2980B9', 'accent': '#FFFFFF'},
            'red': {'primary': '#E74C3C', 'secondary': '#C0392B', 'accent': '#FFFFFF'},
            'green': {'primary': '#2ECC71', 'secondary': '#27AE60', 'accent': '#FFFFFF'},
            'purple': {'primary': '#9B59B6', 'secondary': '#8E44AD', 'accent': '#FFFFFF'},
            'orange': {'primary': '#F39C12', 'secondary': '#E67E22', 'accent': '#FFFFFF'}
        }
        
        logger.info(f"AI Thumbnail Generator initialized with backend: {self.api_backend}")
    
    def generate_thumbnail_image(self, thumbnail_text: str, style: Dict[str, Any] = None, 
                                output_path: str = None) -> str:
        """
        Generate a thumbnail image with overlay text.
        
        Args:
            thumbnail_text (str): Text to overlay on thumbnail (5-6 words max)
            style (dict, optional): Style configuration
            output_path (str, optional): Custom output path
            
        Returns:
            str: Path to generated thumbnail image
            
        Raises:
            Exception: If all generation methods fail
        """
        try:
            logger.info(f"Generating thumbnail for text: '{thumbnail_text}'")
            
            # Validate input
            if not thumbnail_text or not thumbnail_text.strip():
                raise ValueError("Thumbnail text cannot be empty")
            
            thumbnail_text = thumbnail_text.strip()
            
            # Set default style
            if style is None:
                style = {'tone': 'professional'}
            
            # Generate output path if not provided
            if output_path is None:
                safe_text = "".join(c for c in thumbnail_text if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_text = safe_text.replace(' ', '_')[:30]
                timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
                output_path = THUMBNAILS_DIR / f"thumbnail_{safe_text}_{timestamp}.png"
            else:
                output_path = Path(output_path)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Try different generation methods
            success = False
            
            if self.api_backend == 'dall-e' and self.openai_api_key:
                try:
                    success = self._generate_with_dalle(thumbnail_text, style, output_path)
                except Exception as e:
                    logger.warning(f"DALL-E generation failed: {e}")
            
            elif self.api_backend == 'stable-diffusion' and self.huggingface_token:
                try:
                    success = self._generate_with_stable_diffusion(thumbnail_text, style, output_path)
                except Exception as e:
                    logger.warning(f"Stable Diffusion generation failed: {e}")
            
            # Fallback to PIL generation
            if not success:
                logger.info("Using PIL fallback for thumbnail generation")
                success = self._generate_with_pil(thumbnail_text, style, output_path)
            
            if success:
                logger.info(f"Successfully generated thumbnail: {output_path}")
                return str(output_path)
            else:
                raise Exception("All thumbnail generation methods failed")
                
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            raise
    
    def _generate_with_dalle(self, text: str, style: Dict[str, Any], output_path: Path) -> bool:
        """Generate thumbnail using DALL-E API."""
        try:
            import openai
            
            # Configure OpenAI
            openai.api_key = self.openai_api_key
            
            # Get style configuration
            tone = style.get('tone', 'professional')
            style_config = self.style_configs.get(tone, self.style_configs['professional'])
            color_scheme = style.get('color_scheme', 'blue')
            
            # Build prompt
            prompt = f"""Create a YouTube thumbnail background image in {style_config['prompt_style']} style. 
            The image should be suitable for overlaying the text "{text}". 
            Use {color_scheme} color scheme. 
            No text in the image - just background. 
            High quality, 16:9 aspect ratio, professional YouTube thumbnail style."""
            
            # Generate image
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024",
                response_format="url"
            )
            
            # Download and process image
            image_url = response['data'][0]['url']
            image_response = requests.get(image_url, timeout=30)
            image_response.raise_for_status()
            
            # Open and resize image
            background = Image.open(io.BytesIO(image_response.content))
            background = background.resize(self.thumbnail_size, Image.Resampling.LANCZOS)
            
            # Add text overlay
            final_image = self._add_text_overlay(background, text, style)
            
            # Save image
            final_image.save(output_path, 'PNG', quality=95)
            
            return True
            
        except Exception as e:
            logger.error(f"DALL-E generation error: {e}")
            return False
    
    def _generate_with_stable_diffusion(self, text: str, style: Dict[str, Any], output_path: Path) -> bool:
        """Generate thumbnail using Stable Diffusion via Hugging Face."""
        try:
            # Get style configuration
            tone = style.get('tone', 'professional')
            style_config = self.style_configs.get(tone, self.style_configs['professional'])
            color_scheme = style.get('color_scheme', 'blue')
            
            # Build prompt
            prompt = f"""YouTube thumbnail background, {style_config['prompt_style']}, 
            {color_scheme} colors, no text, clean background for text overlay, 
            high quality, professional, 16:9 aspect ratio"""
            
            # Hugging Face Inference API
            api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
            headers = {"Authorization": f"Bearer {self.huggingface_token}"}
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "width": 1024,
                    "height": 576,
                    "num_inference_steps": 20
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            # Process image
            background = Image.open(io.BytesIO(response.content))
            background = background.resize(self.thumbnail_size, Image.Resampling.LANCZOS)
            
            # Add text overlay
            final_image = self._add_text_overlay(background, text, style)
            
            # Save image
            final_image.save(output_path, 'PNG', quality=95)
            
            return True
            
        except Exception as e:
            logger.error(f"Stable Diffusion generation error: {e}")
            return False
    
    def _generate_with_pil(self, text: str, style: Dict[str, Any], output_path: Path) -> bool:
        """Generate thumbnail using PIL with gradient background."""
        try:
            # Get style configuration
            tone = style.get('tone', 'professional')
            style_config = self.style_configs.get(tone, self.style_configs['professional'])
            color_scheme_name = style.get('color_scheme', 'blue')
            color_scheme = self.color_schemes.get(color_scheme_name, self.color_schemes['blue'])
            
            # Create gradient background
            background = self._create_gradient_background(
                self.thumbnail_size,
                color_scheme['primary'],
                color_scheme['secondary']
            )
            
            # Add decorative elements
            background = self._add_decorative_elements(background, color_scheme)
            
            # Add text overlay
            final_image = self._add_text_overlay(background, text, style)
            
            # Save image
            final_image.save(output_path, 'PNG', quality=95)
            
            return True
            
        except Exception as e:
            logger.error(f"PIL generation error: {e}")
            return False
    
    def _create_gradient_background(self, size: Tuple[int, int], color1: str, color2: str) -> Image.Image:
        """Create a gradient background."""
        # Convert hex colors to RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        
        # Create gradient
        width, height = size
        image = Image.new('RGB', size)
        
        for y in range(height):
            # Calculate blend ratio
            ratio = y / height
            
            # Interpolate colors
            r = int(rgb1[0] * (1 - ratio) + rgb2[0] * ratio)
            g = int(rgb1[1] * (1 - ratio) + rgb2[1] * ratio)
            b = int(rgb1[2] * (1 - ratio) + rgb2[2] * ratio)
            
            # Draw line
            for x in range(width):
                image.putpixel((x, y), (r, g, b))
        
        return image
    
    def _add_decorative_elements(self, image: Image.Image, color_scheme: Dict[str, str]) -> Image.Image:
        """Add decorative elements to background."""
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Convert hex to RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        accent_rgb = hex_to_rgb(color_scheme['accent'])
        
        # Add subtle geometric shapes
        # Corner triangles
        triangle_size = 100
        
        # Top-left triangle
        draw.polygon([
            (0, 0),
            (triangle_size, 0),
            (0, triangle_size)
        ], fill=(*accent_rgb, 30))
        
        # Bottom-right triangle
        draw.polygon([
            (width, height),
            (width - triangle_size, height),
            (width, height - triangle_size)
        ], fill=(*accent_rgb, 30))
        
        # Add subtle circles
        circle_radius = 150
        circle_alpha = 20
        
        # Top-right circle
        draw.ellipse([
            width - circle_radius, -circle_radius//2,
            width + circle_radius//2, circle_radius//2
        ], fill=(*accent_rgb, circle_alpha))
        
        # Bottom-left circle
        draw.ellipse([
            -circle_radius//2, height - circle_radius//2,
            circle_radius//2, height + circle_radius//2
        ], fill=(*accent_rgb, circle_alpha))
        
        return image
    
    def _add_text_overlay(self, background: Image.Image, text: str, style: Dict[str, Any]) -> Image.Image:
        """Add text overlay to background image."""
        # Get style configuration
        tone = style.get('tone', 'professional')
        style_config = self.style_configs.get(tone, self.style_configs['professional'])
        
        # Create a copy to work with
        image = background.copy()
        draw = ImageDraw.Draw(image)
        
        # Try to load custom font, fallback to default
        font_size = 72
        try:
            # Try to load a bold font
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.load_default()
                    font_size = 40  # Smaller for default font
                except:
                    font = None
        
        # Calculate text position
        if font:
            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            # Estimate text size for default font
            text_width = len(text) * 20
            text_height = 30
        
        # Position text in lower third of image
        x = (image.width - text_width) // 2
        y = int(image.height * 0.7) - text_height // 2
        
        # Add text shadow for better readability
        shadow_offset = 3
        draw.text((x + shadow_offset, y + shadow_offset), text, 
                 fill=(0, 0, 0, 180), font=font)
        
        # Add main text
        text_color = style_config['text_color']
        if text_color.startswith('#'):
            # Convert hex to RGB
            text_color = text_color.lstrip('#')
            text_color = tuple(int(text_color[i:i+2], 16) for i in (0, 2, 4))
        else:
            text_color = (255, 255, 255)  # Default white
        
        draw.text((x, y), text, fill=text_color, font=font)
        
        # Add accent border/outline if needed
        accent_color = style_config.get('accent_color', '#FFFFFF')
        if accent_color.startswith('#'):
            accent_color = accent_color.lstrip('#')
            accent_rgb = tuple(int(accent_color[i:i+2], 16) for i in (0, 2, 4))
            
            # Draw text outline
            outline_width = 2
            for adj_x in range(-outline_width, outline_width + 1):
                for adj_y in range(-outline_width, outline_width + 1):
                    if adj_x != 0 or adj_y != 0:
                        draw.text((x + adj_x, y + adj_y), text, 
                                fill=accent_rgb, font=font)
            
            # Redraw main text on top
            draw.text((x, y), text, fill=text_color, font=font)
        
        return image
    
    def generate_thumbnails_for_ideas(self, ideas: List[Dict[str, Any]], 
                                    style: Dict[str, Any] = None, 
                                    out_dir: str = 'thumbnails/') -> List[Dict[str, Any]]:
        """
        Generate thumbnails for multiple video ideas.
        
        Args:
            ideas (List[dict]): List of video ideas with thumbnail_texts
            style (dict, optional): Style configuration
            out_dir (str): Output directory for thumbnails
            
        Returns:
            List[dict]: Enhanced ideas with thumbnail_image_path added
        """
        try:
            logger.info(f"Generating thumbnails for {len(ideas)} video ideas")
            
            # Ensure output directory exists
            out_path = Path(out_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            
            enhanced_ideas = []
            
            for i, idea in enumerate(ideas):
                try:
                    # Get first thumbnail text
                    thumbnail_texts = idea.get('thumbnail_texts', [])
                    if not thumbnail_texts:
                        logger.warning(f"Idea {i+1} has no thumbnail texts, skipping")
                        enhanced_idea = idea.copy()
                        enhanced_idea['thumbnail_image_path'] = None
                        enhanced_ideas.append(enhanced_idea)
                        continue
                    
                    thumbnail_text = thumbnail_texts[0]
                    
                    # Generate safe filename
                    title = idea.get('title', f'idea_{i+1}')
                    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_title = safe_title.replace(' ', '_')[:30]
                    
                    output_path = out_path / f"thumbnail_{safe_title}_{i+1}.png"
                    
                    # Generate thumbnail
                    thumbnail_path = self.generate_thumbnail_image(
                        thumbnail_text, style, str(output_path)
                    )
                    
                    # Add path to idea
                    enhanced_idea = idea.copy()
                    enhanced_idea['thumbnail_image_path'] = thumbnail_path
                    enhanced_ideas.append(enhanced_idea)
                    
                    logger.info(f"Generated thumbnail {i+1}/{len(ideas)}: {thumbnail_path}")
                    
                except Exception as e:
                    logger.error(f"Error generating thumbnail for idea {i+1}: {e}")
                    # Add idea without thumbnail path
                    enhanced_idea = idea.copy()
                    enhanced_idea['thumbnail_image_path'] = None
                    enhanced_ideas.append(enhanced_idea)
            
            logger.info(f"Successfully generated thumbnails for {len([i for i in enhanced_ideas if i.get('thumbnail_image_path')])}/{len(ideas)} ideas")
            return enhanced_ideas
            
        except Exception as e:
            logger.error(f"Error in batch thumbnail generation: {e}")
            # Return original ideas without thumbnail paths
            return [dict(idea, thumbnail_image_path=None) for idea in ideas]

# Utility functions for easy integration

def generate_thumbnail_image(thumbnail_text: str, style: Dict[str, Any] = None, 
                           output_path: str = None) -> str:
    """
    Convenience function to generate a single thumbnail image.
    
    Args:
        thumbnail_text (str): Text to overlay on thumbnail
        style (dict, optional): Style configuration
        output_path (str, optional): Custom output path
        
    Returns:
        str: Path to generated thumbnail image
    """
    generator = AIThumbnailGenerator()
    return generator.generate_thumbnail_image(thumbnail_text, style, output_path)

def generate_thumbnails_for_ideas(ideas: List[Dict[str, Any]], 
                                style: Dict[str, Any] = None, 
                                out_dir: str = 'thumbnails/') -> List[Dict[str, Any]]:
    """
    Convenience function to generate thumbnails for multiple ideas.
    
    Args:
        ideas (List[dict]): List of video ideas
        style (dict, optional): Style configuration
        out_dir (str): Output directory
        
    Returns:
        List[dict]: Enhanced ideas with thumbnail paths
    """
    generator = AIThumbnailGenerator()
    return generator.generate_thumbnails_for_ideas(ideas, style, out_dir)

def main():
    """
    Example usage of the AI Thumbnail Generator.
    """
    try:
        # Example video ideas with thumbnail texts
        sample_ideas = [
            {
                'title': 'Ultimate Guide to Cooking Perfect Rice',
                'thumbnail_texts': ['SECRET REVEALED', 'PERFECT RICE', 'CHEF TIPS']
            },
            {
                'title': 'Study Abroad Secrets Nobody Tells You',
                'thumbnail_texts': ['HIDDEN SECRETS', 'STUDY ABROAD', 'MUST KNOW']
            }
        ]
        
        # Example style configuration
        sample_style = {
            'tone': 'professional',
            'color_scheme': 'blue',
            'font_style': 'bold'
        }
        
        print("AI Thumbnail Generator Example")
        print("=" * 40)
        
        # Generate thumbnails
        generator = AIThumbnailGenerator()
        enhanced_ideas = generator.generate_thumbnails_for_ideas(sample_ideas, sample_style)
        
        # Display results
        print(f"\n🎨 GENERATED THUMBNAILS")
        
        for i, idea in enumerate(enhanced_ideas, 1):
            print(f"\n📹 IDEA {i}: {idea['title'][:50]}...")
            if idea.get('thumbnail_image_path'):
                print(f"🖼️  Thumbnail: {idea['thumbnail_image_path']}")
            else:
                print(f"❌ Thumbnail generation failed")
        
        print(f"\nThumbnails saved in: {THUMBNAILS_DIR}")
        
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Main execution error: {e}")

if __name__ == "__main__":
    # Import pandas for timestamp (used in generate_thumbnail_image)
    import pandas as pd
    main()