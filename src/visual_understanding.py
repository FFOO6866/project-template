"""
Visual Understanding Module for Horme Product Enhancement.

This module provides advanced visual analysis capabilities to enhance product data:
1. Diagram analyzer for installation guides and technical drawings
2. Tool identification from images and videos
3. Safety hazard detection in DIY project images
4. Assembly sequence extraction from visual content
5. Before/after comparison analysis
6. Component recognition and measurement extraction

Architecture:
- Built on Kailash Core SDK for workflow integration
- Uses computer vision and AI for image analysis
- Supports multiple image formats and video frames
- Integrates with product database for contextual understanding
- Provides confidence scoring for all visual interpretations
"""

import os
import json
import logging
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import hashlib
import cv2
import numpy as np

# Kailash SDK imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Computer Vision libraries
try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("Warning: OpenCV and PIL not available. Computer vision features disabled.")

# AI/ML libraries for advanced analysis
try:
    import torch
    import torchvision.transforms as transforms
    from transformers import pipeline, BlipProcessor, BlipForConditionalGeneration
    HAS_AI_MODELS = True
except ImportError:
    HAS_AI_MODELS = False
    print("Warning: PyTorch and Transformers not available. AI analysis features disabled.")

# OCR for text extraction
try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("Warning: pytesseract not available. OCR features disabled.")


class ImageType(Enum):
    """Types of images we can analyze."""
    PRODUCT_PHOTO = "product_photo"
    INSTALLATION_DIAGRAM = "installation_diagram"
    TECHNICAL_DRAWING = "technical_drawing"
    SAFETY_DIAGRAM = "safety_diagram"
    STEP_BY_STEP = "step_by_step"
    BEFORE_AFTER = "before_after"
    TOOL_IDENTIFICATION = "tool_identification"
    MEASUREMENT_DIAGRAM = "measurement_diagram"
    WIRING_DIAGRAM = "wiring_diagram"
    ASSEMBLY_GUIDE = "assembly_guide"


class AnalysisType(Enum):
    """Types of visual analysis we can perform."""
    OBJECT_DETECTION = "object_detection"
    TEXT_EXTRACTION = "text_extraction"
    MEASUREMENT_EXTRACTION = "measurement_extraction"
    SAFETY_ANALYSIS = "safety_analysis"
    SEQUENCE_ANALYSIS = "sequence_analysis"
    COMPARISON_ANALYSIS = "comparison_analysis"
    TOOL_RECOGNITION = "tool_recognition"
    COMPONENT_IDENTIFICATION = "component_identification"


class SafetyLevel(Enum):
    """Safety levels detected in images."""
    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"
    DANGER = "danger"
    EXTREME_DANGER = "extreme_danger"


@dataclass
class DetectedObject:
    """Object detected in an image."""
    object_type: str
    confidence: float
    bounding_box: Tuple[int, int, int, int]  # (x, y, width, height)
    attributes: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class ExtractedText:
    """Text extracted from an image."""
    text: str
    confidence: float
    location: Tuple[int, int, int, int]  # (x, y, width, height)
    font_size: Optional[int] = None
    is_measurement: bool = False
    is_label: bool = False


@dataclass
class SafetyHazard:
    """Safety hazard detected in an image."""
    hazard_type: str
    severity: SafetyLevel
    location: Tuple[int, int, int, int]
    description: str
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class AssemblyStep:
    """Step in an assembly sequence."""
    step_number: int
    description: str
    tools_required: List[str] = field(default_factory=list)
    components_involved: List[str] = field(default_factory=list)
    safety_notes: List[str] = field(default_factory=list)
    estimated_time: Optional[str] = None
    difficulty: Optional[str] = None


@dataclass
class Measurement:
    """Measurement extracted from an image."""
    value: float
    unit: str
    measurement_type: str  # length, width, height, diameter, angle, etc.
    location: Tuple[int, int, int, int]
    confidence: float
    context: str = ""  # What is being measured


@dataclass
class VisualAnalysisResult:
    """Complete visual analysis result for an image."""
    
    # Basic Information
    image_id: str
    image_path: str
    image_type: ImageType
    analysis_types: List[AnalysisType]
    
    # Image Properties
    width: int
    height: int
    channels: int
    file_size: int
    format: str
    
    # Analysis Results
    detected_objects: List[DetectedObject] = field(default_factory=list)
    extracted_text: List[ExtractedText] = field(default_factory=list)
    measurements: List[Measurement] = field(default_factory=list)
    safety_hazards: List[SafetyHazard] = field(default_factory=list)
    assembly_steps: List[AssemblyStep] = field(default_factory=list)
    
    # AI-Generated Descriptions
    overall_description: str = ""
    technical_summary: str = ""
    safety_summary: str = ""
    
    # Product Relations
    identified_tools: List[str] = field(default_factory=list)
    identified_materials: List[str] = field(default_factory=list)
    identified_brands: List[str] = field(default_factory=list)
    related_skus: List[str] = field(default_factory=list)
    
    # Quality Metrics
    image_quality_score: float = 0.0  # 0-1 scale
    analysis_confidence: float = 0.0  # 0-1 scale
    completeness_score: float = 0.0   # 0-1 scale
    
    # Processing Metadata
    analyzed_at: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0
    analysis_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class VisualAnalysisConfig:
    """Configuration for visual analysis."""
    
    # AI Model Settings
    use_ai_models: bool = True
    device: str = "cpu"  # or "cuda" if available
    model_cache_dir: str = "model_cache"
    
    # Analysis Settings
    min_object_confidence: float = 0.5
    min_text_confidence: float = 0.7
    enable_ocr: bool = True
    enable_safety_detection: bool = True
    enable_measurement_extraction: bool = True
    
    # Image Processing
    max_image_size: Tuple[int, int] = (1920, 1080)
    supported_formats: List[str] = field(default_factory=lambda: ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'])
    
    # Output Settings
    save_annotated_images: bool = True
    annotation_output_dir: str = "annotated_images"
    cache_analysis_results: bool = True
    cache_duration_hours: int = 24
    
    # Performance
    batch_size: int = 1
    max_processing_time: float = 300.0  # 5 minutes max per image


class VisualUnderstandingModule:
    """
    Advanced visual understanding for DIY product enhancement.
    
    This module analyzes images and videos to extract practical knowledge that
    enhances basic product information with visual context, safety information,
    and assembly guidance.
    """
    
    def __init__(self, config: VisualAnalysisConfig):
        self.config = config
        self.logger = logging.getLogger("visual_understanding")
        self.logger.setLevel(logging.INFO)
        
        # Initialize Kailash components
        self.workflow = WorkflowBuilder()
        self.runtime = LocalRuntime()
        
        # Create directories
        Path(self.config.model_cache_dir).mkdir(exist_ok=True)
        Path(self.config.annotation_output_dir).mkdir(exist_ok=True)
        
        # Initialize AI models
        self._initialize_ai_models()
        
        # Analysis results storage
        self.analysis_cache: Dict[str, VisualAnalysisResult] = {}
        
        # Knowledge databases
        self._initialize_visual_knowledge_bases()
    
    def _initialize_ai_models(self) -> None:
        """Initialize AI models for visual analysis."""
        self.models = {}
        
        if not HAS_AI_MODELS or not self.config.use_ai_models:
            self.logger.info("AI models disabled or not available")
            return
        
        try:
            # Initialize BLIP for image captioning
            self.models['caption_processor'] = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.models['caption_model'] = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            
            # Initialize object detection (simplified - would use YOLO or similar in production)
            # For now, we'll use a classification model as a placeholder
            self.models['classifier'] = pipeline("image-classification", model="google/vit-base-patch16-224")
            
            self.logger.info("AI models initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize AI models: {e}")
            self.models = {}
    
    def _initialize_visual_knowledge_bases(self) -> None:
        """Initialize knowledge bases for visual recognition."""
        
        # Common tools that appear in DIY images
        self.visual_tool_patterns = {
            "drill": ["circular object with bits", "power tool with chuck", "cordless drill"],
            "saw": ["blade tool", "cutting tool", "circular saw", "hand saw"],
            "hammer": ["handle with head", "striking tool", "claw hammer"],
            "screwdriver": ["handle with shaft", "flathead", "phillips head"],
            "wrench": ["adjustable wrench", "combination wrench", "socket wrench"],
            "level": ["bubble level", "spirit level", "long straight tool"],
            "measuring tape": ["retractable tape", "tape measure", "ruler"],
            "pliers": ["gripping tool", "needle nose", "channel lock"]
        }
        
        # Safety equipment patterns
        self.safety_equipment_patterns = {
            "safety glasses": ["protective eyewear", "safety goggles"],
            "hard hat": ["protective helmet", "construction helmet"],
            "work gloves": ["protective gloves", "work gloves"],
            "safety vest": ["high visibility vest", "reflective vest"],
            "ear protection": ["earplugs", "ear muffs", "hearing protection"]
        }
        
        # Hazard detection patterns
        self.hazard_patterns = {
            "electrical": ["exposed wires", "electrical panel", "live wires", "electrical outlet"],
            "sharp_objects": ["saw blade", "sharp edge", "cutting tool", "knife"],
            "height": ["ladder", "scaffolding", "elevated surface", "working at height"],
            "chemicals": ["chemical container", "spray bottle", "paint can", "solvent"],
            "heavy_objects": ["lifting", "heavy equipment", "crane", "hoist"]
        }
        
        # Measurement patterns
        self.measurement_patterns = {
            "length": r'(\d+(?:\.\d+)?)\s*(?:"|\'|in|inch|inches|ft|feet|cm|mm)',
            "angle": r'(\d+(?:\.\d+)?)\s*(?:°|deg|degree|degrees)',
            "diameter": r'(\d+(?:\.\d+)?)\s*(?:"|\'|in|inch|inches|cm|mm)\s*(?:dia|diameter)',
            "weight": r'(\d+(?:\.\d+)?)\s*(?:lb|lbs|pound|pounds|kg|kilogram|oz|ounce)'
        }
        
        # Assembly sequence indicators
        self.sequence_indicators = [
            "step 1", "step 2", "step 3", "first", "second", "third", "next", "then",
            "finally", "before", "after", "attach", "connect", "install", "remove"
        ]
    
    def analyze_image(self, image_path: str, image_type: ImageType = None, 
                     analysis_types: List[AnalysisType] = None) -> VisualAnalysisResult:
        """
        Perform comprehensive visual analysis on an image.
        
        Args:
            image_path: Path to the image file
            image_type: Type of image for context-specific analysis
            analysis_types: Specific types of analysis to perform
        
        Returns:
            VisualAnalysisResult: Complete analysis results
        """
        start_time = datetime.now()
        
        # Generate unique image ID
        image_id = hashlib.md5(f"{image_path}_{start_time}".encode()).hexdigest()[:16]
        
        # Check cache first
        cache_key = f"{image_path}_{image_type}_{hash(tuple(analysis_types) if analysis_types else ())}"
        if cache_key in self.analysis_cache:
            cached_result = self.analysis_cache[cache_key]
            cache_age = datetime.now() - cached_result.analyzed_at
            if cache_age.total_seconds() < self.config.cache_duration_hours * 3600:
                self.logger.info(f"Using cached analysis for {image_path}")
                return cached_result
        
        try:
            # Load and validate image
            if not HAS_CV2:
                raise Exception("OpenCV not available for image processing")
            
            image = cv2.imread(str(image_path))
            if image is None:
                raise Exception(f"Could not load image: {image_path}")
            
            # Get image properties
            height, width, channels = image.shape
            file_size = os.path.getsize(image_path)
            format_ext = Path(image_path).suffix.lower()
            
            # Initialize result
            result = VisualAnalysisResult(
                image_id=image_id,
                image_path=str(image_path),
                image_type=image_type or ImageType.PRODUCT_PHOTO,
                analysis_types=analysis_types or [AnalysisType.OBJECT_DETECTION, AnalysisType.TEXT_EXTRACTION],
                width=width,
                height=height,
                channels=channels,
                file_size=file_size,
                format=format_ext
            )
            
            # Perform requested analyses
            if AnalysisType.OBJECT_DETECTION in result.analysis_types:
                result.detected_objects = self._detect_objects(image)
            
            if AnalysisType.TEXT_EXTRACTION in result.analysis_types:
                result.extracted_text = self._extract_text(image)
            
            if AnalysisType.MEASUREMENT_EXTRACTION in result.analysis_types:
                result.measurements = self._extract_measurements(image, result.extracted_text)
            
            if AnalysisType.SAFETY_ANALYSIS in result.analysis_types:
                result.safety_hazards = self._analyze_safety_hazards(image, result.detected_objects)
            
            if AnalysisType.SEQUENCE_ANALYSIS in result.analysis_types:
                result.assembly_steps = self._analyze_assembly_sequence(image, result.extracted_text)
            
            if AnalysisType.TOOL_RECOGNITION in result.analysis_types:
                result.identified_tools = self._recognize_tools(image, result.detected_objects)
            
            # Generate AI descriptions if models available
            if self.models and 'caption_model' in self.models:
                result.overall_description = self._generate_image_description(image)
                result.technical_summary = self._generate_technical_summary(result)
                result.safety_summary = self._generate_safety_summary(result)
            
            # Calculate quality metrics
            result.image_quality_score = self._calculate_image_quality(image)
            result.analysis_confidence = self._calculate_analysis_confidence(result)
            result.completeness_score = self._calculate_completeness_score(result)
            
            # Record processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            # Save annotated image if requested
            if self.config.save_annotated_images:
                self._save_annotated_image(image, result)
            
            # Cache result
            if self.config.cache_analysis_results:
                self.analysis_cache[cache_key] = result
            
            self.logger.info(f"Image analysis completed for {image_path} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing image {image_path}: {e}")
            # Return minimal result with error information
            return VisualAnalysisResult(
                image_id=image_id,
                image_path=str(image_path),
                image_type=image_type or ImageType.PRODUCT_PHOTO,
                analysis_types=analysis_types or [],
                width=0, height=0, channels=0, file_size=0, format="",
                overall_description=f"Analysis failed: {str(e)}"
            )
    
    def _detect_objects(self, image: np.ndarray) -> List[DetectedObject]:
        """Detect objects in the image."""
        objects = []
        
        if not self.models or 'classifier' not in self.models:
            # Fallback to basic object detection using OpenCV
            return self._detect_objects_opencv(image)
        
        try:
            # Convert OpenCV image to PIL
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            
            # Use AI model for classification
            predictions = self.models['classifier'](pil_image)
            
            for pred in predictions[:5]:  # Top 5 predictions
                if pred['score'] > self.config.min_object_confidence:
                    obj = DetectedObject(
                        object_type=pred['label'],
                        confidence=pred['score'],
                        bounding_box=(0, 0, image.shape[1], image.shape[0]),  # Full image for now
                        description=f"Detected {pred['label']} with {pred['score']:.2f} confidence"
                    )
                    objects.append(obj)
            
        except Exception as e:
            self.logger.warning(f"AI object detection failed: {e}")
            return self._detect_objects_opencv(image)
        
        return objects
    
    def _detect_objects_opencv(self, image: np.ndarray) -> List[DetectedObject]:
        """Fallback object detection using OpenCV."""
        objects = []
        
        # Simple object detection using contours and shapes
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for i, contour in enumerate(contours[:10]):  # Top 10 contours
            area = cv2.contourArea(contour)
            if area > 1000:  # Filter small contours
                x, y, w, h = cv2.boundingRect(contour)
                
                # Simple shape classification
                aspect_ratio = w / h
                object_type = "unknown_object"
                
                if 0.8 <= aspect_ratio <= 1.2:
                    object_type = "circular_tool"
                elif aspect_ratio > 3:
                    object_type = "linear_tool"
                elif aspect_ratio < 0.5:
                    object_type = "vertical_object"
                
                obj = DetectedObject(
                    object_type=object_type,
                    confidence=0.6,  # Medium confidence for OpenCV detection
                    bounding_box=(x, y, w, h),
                    attributes={"area": area, "aspect_ratio": aspect_ratio}
                )
                objects.append(obj)
        
        return objects
    
    def _extract_text(self, image: np.ndarray) -> List[ExtractedText]:
        """Extract text from the image using OCR."""
        texts = []
        
        if not HAS_OCR or not self.config.enable_ocr:
            self.logger.info("OCR not available or disabled")
            return texts
        
        try:
            # Preprocess image for better OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding to get a binary image
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Use pytesseract to extract text with bounding boxes
            data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)
            
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                confidence = int(data['conf'][i])
                
                if text and confidence > self.config.min_text_confidence * 100:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    
                    # Classify text type
                    is_measurement = any(pattern in text.lower() for pattern in ['inch', 'ft', 'cm', 'mm', '"', "'"])
                    is_label = len(text) < 20 and not any(char.isdigit() for char in text)
                    
                    extracted_text = ExtractedText(
                        text=text,
                        confidence=confidence / 100.0,
                        location=(x, y, w, h),
                        is_measurement=is_measurement,
                        is_label=is_label
                    )
                    texts.append(extracted_text)
        
        except Exception as e:
            self.logger.warning(f"Text extraction failed: {e}")
        
        return texts
    
    def _extract_measurements(self, image: np.ndarray, extracted_texts: List[ExtractedText]) -> List[Measurement]:
        """Extract measurements from text and visual cues."""
        measurements = []
        
        # Extract from OCR text
        for text_obj in extracted_texts:
            if text_obj.is_measurement:
                for measurement_type, pattern in self.measurement_patterns.items():
                    import re
                    matches = re.findall(pattern, text_obj.text, re.IGNORECASE)
                    for match in matches:
                        try:
                            value = float(match)
                            # Determine unit from text
                            unit = "inches"  # Default
                            if "cm" in text_obj.text.lower():
                                unit = "cm"
                            elif "mm" in text_obj.text.lower():
                                unit = "mm"
                            elif "ft" in text_obj.text.lower():
                                unit = "feet"
                            
                            measurement = Measurement(
                                value=value,
                                unit=unit,
                                measurement_type=measurement_type,
                                location=text_obj.location,
                                confidence=text_obj.confidence,
                                context=text_obj.text
                            )
                            measurements.append(measurement)
                            
                        except ValueError:
                            continue
        
        return measurements
    
    def _analyze_safety_hazards(self, image: np.ndarray, detected_objects: List[DetectedObject]) -> List[SafetyHazard]:
        """Analyze image for safety hazards."""
        hazards = []
        
        if not self.config.enable_safety_detection:
            return hazards
        
        # Check detected objects for hazards
        for obj in detected_objects:
            hazard_type = None
            severity = SafetyLevel.SAFE
            recommendations = []
            
            obj_name = obj.object_type.lower()
            
            # Check for sharp objects
            if any(sharp in obj_name for sharp in ["saw", "blade", "knife", "sharp"]):
                hazard_type = "sharp_object"
                severity = SafetyLevel.WARNING
                recommendations = ["Wear safety gloves", "Handle with care"]
            
            # Check for electrical hazards
            elif any(elec in obj_name for elec in ["wire", "electrical", "outlet", "panel"]):
                hazard_type = "electrical"
                severity = SafetyLevel.DANGER
                recommendations = ["Turn off power", "Use insulated tools", "Wear safety gear"]
            
            # Check for height-related hazards
            elif any(height in obj_name for height in ["ladder", "scaffold", "elevated"]):
                hazard_type = "height"
                severity = SafetyLevel.CAUTION
                recommendations = ["Use fall protection", "Ensure stable footing", "Have spotter"]
            
            if hazard_type:
                hazard = SafetyHazard(
                    hazard_type=hazard_type,
                    severity=severity,
                    location=obj.bounding_box,
                    description=f"{hazard_type.replace('_', ' ').title()} detected",
                    recommendations=recommendations,
                    confidence=obj.confidence
                )
                hazards.append(hazard)
        
        return hazards
    
    def _analyze_assembly_sequence(self, image: np.ndarray, extracted_texts: List[ExtractedText]) -> List[AssemblyStep]:
        """Analyze image for assembly sequence information."""
        steps = []
        
        # Look for step indicators in text
        step_texts = []
        for text_obj in extracted_texts:
            text_lower = text_obj.text.lower()
            if any(indicator in text_lower for indicator in self.sequence_indicators):
                step_texts.append(text_obj)
        
        # Extract step information
        for i, text_obj in enumerate(step_texts):
            step_number = i + 1
            
            # Try to extract step number from text
            import re
            step_match = re.search(r'step\s*(\d+)', text_obj.text.lower())
            if step_match:
                step_number = int(step_match.group(1))
            
            # Identify tools mentioned in step
            tools_mentioned = []
            for tool_name in self.visual_tool_patterns.keys():
                if tool_name in text_obj.text.lower():
                    tools_mentioned.append(tool_name)
            
            step = AssemblyStep(
                step_number=step_number,
                description=text_obj.text,
                tools_required=tools_mentioned,
                difficulty="intermediate"  # Default
            )
            steps.append(step)
        
        return sorted(steps, key=lambda x: x.step_number)
    
    def _recognize_tools(self, image: np.ndarray, detected_objects: List[DetectedObject]) -> List[str]:
        """Recognize tools in the image."""
        tools = []
        
        # Check detected objects against tool patterns
        for obj in detected_objects:
            obj_name = obj.object_type.lower()
            
            for tool_name, patterns in self.visual_tool_patterns.items():
                if any(pattern in obj_name for pattern in patterns):
                    if tool_name not in tools:
                        tools.append(tool_name)
        
        return tools
    
    def _generate_image_description(self, image: np.ndarray) -> str:
        """Generate AI description of the image."""
        if not self.models or 'caption_model' not in self.models:
            return "AI description not available"
        
        try:
            # Convert to PIL Image
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            
            # Generate caption
            inputs = self.models['caption_processor'](pil_image, return_tensors="pt")
            out = self.models['caption_model'].generate(**inputs, max_length=50)
            caption = self.models['caption_processor'].decode(out[0], skip_special_tokens=True)
            
            return caption
            
        except Exception as e:
            self.logger.warning(f"AI caption generation failed: {e}")
            return "Description generation failed"
    
    def _generate_technical_summary(self, result: VisualAnalysisResult) -> str:
        """Generate technical summary from analysis results."""
        summary_parts = []
        
        if result.detected_objects:
            summary_parts.append(f"Detected {len(result.detected_objects)} objects")
        
        if result.identified_tools:
            summary_parts.append(f"Tools identified: {', '.join(result.identified_tools)}")
        
        if result.measurements:
            summary_parts.append(f"Contains {len(result.measurements)} measurements")
        
        if result.assembly_steps:
            summary_parts.append(f"Shows {len(result.assembly_steps)} assembly steps")
        
        return ". ".join(summary_parts) if summary_parts else "No technical details extracted"
    
    def _generate_safety_summary(self, result: VisualAnalysisResult) -> str:
        """Generate safety summary from analysis results."""
        if not result.safety_hazards:
            return "No safety hazards detected"
        
        hazard_counts = {}
        for hazard in result.safety_hazards:
            hazard_counts[hazard.severity.value] = hazard_counts.get(hazard.severity.value, 0) + 1
        
        summary_parts = []
        for severity, count in hazard_counts.items():
            summary_parts.append(f"{count} {severity} hazard(s)")
        
        return "Safety concerns: " + ", ".join(summary_parts)
    
    def _calculate_image_quality(self, image: np.ndarray) -> float:
        """Calculate image quality score."""
        # Simple quality metrics
        # Sharpness (Laplacian variance)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(sharpness / 1000, 1.0)  # Normalize
        
        # Brightness (mean pixel value)
        brightness = np.mean(gray) / 255.0
        brightness_score = 1.0 - abs(brightness - 0.5) * 2  # Optimal around 0.5
        
        # Contrast (standard deviation)
        contrast = np.std(gray) / 255.0
        contrast_score = min(contrast * 4, 1.0)  # Normalize
        
        # Combined quality score
        quality_score = (sharpness_score + brightness_score + contrast_score) / 3
        return quality_score
    
    def _calculate_analysis_confidence(self, result: VisualAnalysisResult) -> float:
        """Calculate overall confidence in the analysis."""
        confidence_factors = []
        
        # Object detection confidence
        if result.detected_objects:
            avg_obj_confidence = sum(obj.confidence for obj in result.detected_objects) / len(result.detected_objects)
            confidence_factors.append(avg_obj_confidence)
        
        # Text extraction confidence
        if result.extracted_text:
            avg_text_confidence = sum(text.confidence for text in result.extracted_text) / len(result.extracted_text)
            confidence_factors.append(avg_text_confidence)
        
        # Image quality factor
        confidence_factors.append(result.image_quality_score)
        
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
    
    def _calculate_completeness_score(self, result: VisualAnalysisResult) -> float:
        """Calculate how complete the analysis is."""
        completeness_factors = []
        
        # Check if each analysis type produced results
        if AnalysisType.OBJECT_DETECTION in result.analysis_types:
            completeness_factors.append(1.0 if result.detected_objects else 0.0)
        
        if AnalysisType.TEXT_EXTRACTION in result.analysis_types:
            completeness_factors.append(1.0 if result.extracted_text else 0.0)
        
        if AnalysisType.MEASUREMENT_EXTRACTION in result.analysis_types:
            completeness_factors.append(1.0 if result.measurements else 0.0)
        
        if AnalysisType.SAFETY_ANALYSIS in result.analysis_types:
            completeness_factors.append(1.0)  # Always complete (may find no hazards)
        
        if AnalysisType.TOOL_RECOGNITION in result.analysis_types:
            completeness_factors.append(1.0 if result.identified_tools else 0.0)
        
        return sum(completeness_factors) / len(completeness_factors) if completeness_factors else 0.0
    
    def _save_annotated_image(self, image: np.ndarray, result: VisualAnalysisResult) -> None:
        """Save image with annotations showing analysis results."""
        try:
            annotated = image.copy()
            
            # Draw bounding boxes for detected objects
            for obj in result.detected_objects:
                x, y, w, h = obj.bounding_box
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(annotated, f"{obj.object_type} ({obj.confidence:.2f})", 
                           (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Draw text regions
            for text in result.extracted_text:
                x, y, w, h = text.location
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 0, 0), 1)
                cv2.putText(annotated, text.text[:20], (x, y - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
            
            # Draw safety hazards
            for hazard in result.safety_hazards:
                x, y, w, h = hazard.location
                color = (0, 0, 255) if hazard.severity in [SafetyLevel.DANGER, SafetyLevel.EXTREME_DANGER] else (0, 165, 255)
                cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 3)
                cv2.putText(annotated, f"HAZARD: {hazard.hazard_type}", 
                           (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Save annotated image
            output_path = Path(self.config.annotation_output_dir) / f"annotated_{result.image_id}.jpg"
            cv2.imwrite(str(output_path), annotated)
            
        except Exception as e:
            self.logger.warning(f"Failed to save annotated image: {e}")
    
    def enhance_product_with_visual_knowledge(self, product_sku: str, product_data: Dict[str, Any], 
                                            image_paths: List[str] = None) -> Dict[str, Any]:
        """
        Enhance product data with visual analysis insights.
        
        This is the core integration function that enriches basic product information
        with visual understanding, safety analysis, and assembly guidance.
        """
        enhanced_data = product_data.copy()
        
        if not image_paths:
            # Look for images in common locations
            image_paths = self._find_product_images(product_sku, product_data)
        
        if not image_paths:
            enhanced_data["visual_analysis"] = {"status": "no_images_found"}
            return enhanced_data
        
        # Analyze all available images
        visual_analyses = []
        for image_path in image_paths:
            if Path(image_path).exists():
                analysis_types = [
                    AnalysisType.OBJECT_DETECTION,
                    AnalysisType.TEXT_EXTRACTION,
                    AnalysisType.TOOL_RECOGNITION,
                    AnalysisType.SAFETY_ANALYSIS,
                    AnalysisType.MEASUREMENT_EXTRACTION
                ]
                
                # Determine image type from context
                image_type = self._classify_image_type(image_path, product_data)
                
                analysis = self.analyze_image(image_path, image_type, analysis_types)
                visual_analyses.append(analysis)
        
        if visual_analyses:
            # Aggregate insights from all images
            enhanced_data["visual_analysis"] = self._aggregate_visual_insights(visual_analyses)
            
            # Add specific enhancements
            enhanced_data["tool_usage_visual"] = self._extract_tool_usage_insights(visual_analyses)
            enhanced_data["safety_visual_analysis"] = self._extract_safety_insights(visual_analyses)
            enhanced_data["assembly_visual_guide"] = self._extract_assembly_insights(visual_analyses)
            enhanced_data["measurement_specifications"] = self._extract_measurement_insights(visual_analyses)
            enhanced_data["visual_quality_assessment"] = self._assess_visual_quality(visual_analyses)
        
        return enhanced_data
    
    def _find_product_images(self, product_sku: str, product_data: Dict[str, Any]) -> List[str]:
        """Find images related to a product."""
        image_paths = []
        
        # Common image directories
        search_dirs = ["images", "product_images", "uploads", "assets/images"]
        
        for search_dir in search_dirs:
            if Path(search_dir).exists():
                # Look for images matching SKU or product name
                product_name_clean = product_data.get("name", "").lower().replace(" ", "_")
                
                for ext in self.config.supported_formats:
                    # Try SKU-based naming
                    sku_pattern = Path(search_dir) / f"{product_sku}*{ext}"
                    image_paths.extend(str(p) for p in Path(search_dir).glob(f"{product_sku}*{ext}"))
                    
                    # Try name-based naming
                    if product_name_clean:
                        image_paths.extend(str(p) for p in Path(search_dir).glob(f"{product_name_clean}*{ext}"))
        
        return list(set(image_paths))[:5]  # Limit to 5 images
    
    def _classify_image_type(self, image_path: str, product_data: Dict[str, Any]) -> ImageType:
        """Classify image type based on filename and product context."""
        filename = Path(image_path).stem.lower()
        
        if any(word in filename for word in ["install", "assembly", "guide"]):
            return ImageType.INSTALLATION_DIAGRAM
        elif any(word in filename for word in ["diagram", "technical", "drawing"]):
            return ImageType.TECHNICAL_DRAWING
        elif any(word in filename for word in ["safety", "warning"]):
            return ImageType.SAFETY_DIAGRAM
        elif any(word in filename for word in ["step", "sequence"]):
            return ImageType.STEP_BY_STEP
        elif any(word in filename for word in ["before", "after"]):
            return ImageType.BEFORE_AFTER
        elif any(word in filename for word in ["measure", "dimension"]):
            return ImageType.MEASUREMENT_DIAGRAM
        elif any(word in filename for word in ["wire", "electrical"]):
            return ImageType.WIRING_DIAGRAM
        else:
            return ImageType.PRODUCT_PHOTO
    
    def _aggregate_visual_insights(self, analyses: List[VisualAnalysisResult]) -> Dict[str, Any]:
        """Aggregate insights from multiple image analyses."""
        insights = {
            "total_images_analyzed": len(analyses),
            "average_quality_score": sum(a.image_quality_score for a in analyses) / len(analyses),
            "average_confidence": sum(a.analysis_confidence for a in analyses) / len(analyses),
            "total_objects_detected": sum(len(a.detected_objects) for a in analyses),
            "total_text_extracted": sum(len(a.extracted_text) for a in analyses),
            "total_measurements": sum(len(a.measurements) for a in analyses),
            "total_safety_hazards": sum(len(a.safety_hazards) for a in analyses),
            "processing_time_total": sum(a.processing_time for a in analyses)
        }
        
        # Aggregate all detected objects
        all_objects = []
        for analysis in analyses:
            all_objects.extend([obj.object_type for obj in analysis.detected_objects])
        insights["unique_objects"] = list(set(all_objects))
        
        # Aggregate all tools identified
        all_tools = []
        for analysis in analyses:
            all_tools.extend(analysis.identified_tools)
        insights["all_tools_identified"] = list(set(all_tools))
        
        return insights
    
    def _extract_tool_usage_insights(self, analyses: List[VisualAnalysisResult]) -> Dict[str, Any]:
        """Extract tool usage insights from visual analyses."""
        tool_insights = {}
        
        # Collect all tool mentions
        tool_contexts = {}
        for analysis in analyses:
            for tool in analysis.identified_tools:
                if tool not in tool_contexts:
                    tool_contexts[tool] = []
                
                # Add context from this image
                context = {
                    "image_type": analysis.image_type.value,
                    "confidence": analysis.analysis_confidence,
                    "description": analysis.overall_description
                }
                tool_contexts[tool].append(context)
        
        tool_insights["tool_contexts"] = tool_contexts
        tool_insights["most_common_tools"] = sorted(tool_contexts.keys(), 
                                                   key=lambda x: len(tool_contexts[x]), 
                                                   reverse=True)[:5]
        
        return tool_insights
    
    def _extract_safety_insights(self, analyses: List[VisualAnalysisResult]) -> Dict[str, Any]:
        """Extract safety insights from visual analyses."""
        safety_insights = {
            "total_hazards": sum(len(a.safety_hazards) for a in analyses),
            "hazard_types": [],
            "severity_breakdown": {},
            "safety_recommendations": []
        }
        
        for analysis in analyses:
            for hazard in analysis.safety_hazards:
                if hazard.hazard_type not in safety_insights["hazard_types"]:
                    safety_insights["hazard_types"].append(hazard.hazard_type)
                
                severity = hazard.severity.value
                safety_insights["severity_breakdown"][severity] = safety_insights["severity_breakdown"].get(severity, 0) + 1
                
                safety_insights["safety_recommendations"].extend(hazard.recommendations)
        
        # Remove duplicate recommendations
        safety_insights["safety_recommendations"] = list(set(safety_insights["safety_recommendations"]))
        
        return safety_insights
    
    def _extract_assembly_insights(self, analyses: List[VisualAnalysisResult]) -> Dict[str, Any]:
        """Extract assembly insights from visual analyses."""
        assembly_insights = {
            "has_assembly_steps": any(analysis.assembly_steps for analysis in analyses),
            "total_steps": sum(len(a.assembly_steps) for a in analyses),
            "required_tools": [],
            "estimated_difficulty": "intermediate"
        }
        
        all_tools = set()
        for analysis in analyses:
            for step in analysis.assembly_steps:
                all_tools.update(step.tools_required)
        
        assembly_insights["required_tools"] = list(all_tools)
        
        return assembly_insights
    
    def _extract_measurement_insights(self, analyses: List[VisualAnalysisResult]) -> Dict[str, Any]:
        """Extract measurement insights from visual analyses."""
        measurement_insights = {
            "has_measurements": any(analysis.measurements for analysis in analyses),
            "total_measurements": sum(len(a.measurements) for a in analyses),
            "measurement_types": [],
            "units_used": []
        }
        
        for analysis in analyses:
            for measurement in analysis.measurements:
                if measurement.measurement_type not in measurement_insights["measurement_types"]:
                    measurement_insights["measurement_types"].append(measurement.measurement_type)
                
                if measurement.unit not in measurement_insights["units_used"]:
                    measurement_insights["units_used"].append(measurement.unit)
        
        return measurement_insights
    
    def _assess_visual_quality(self, analyses: List[VisualAnalysisResult]) -> Dict[str, Any]:
        """Assess overall visual quality of product images."""
        quality_assessment = {
            "average_image_quality": sum(a.image_quality_score for a in analyses) / len(analyses),
            "analysis_reliability": sum(a.analysis_confidence for a in analyses) / len(analyses),
            "completeness": sum(a.completeness_score for a in analyses) / len(analyses),
            "recommendations": []
        }
        
        # Generate recommendations based on quality
        if quality_assessment["average_image_quality"] < 0.6:
            quality_assessment["recommendations"].append("Consider higher quality images for better analysis")
        
        if quality_assessment["analysis_reliability"] < 0.7:
            quality_assessment["recommendations"].append("Add more detailed images for better product understanding")
        
        if not any(a.measurements for a in analyses):
            quality_assessment["recommendations"].append("Include dimension diagrams for complete specifications")
        
        return quality_assessment
    
    def generate_workflow_for_visual_analysis(self, product_skus: List[str]) -> WorkflowBuilder:
        """Generate a Kailash workflow for bulk visual analysis."""
        workflow = WorkflowBuilder()
        
        # Step 1: Find product images
        workflow.add_node("PythonCodeNode", "find_images", {
            "code": f"""
from visual_understanding import VisualUnderstandingModule, VisualAnalysisConfig
from pathlib import Path

config = VisualAnalysisConfig()
visual_module = VisualUnderstandingModule(config)

product_skus = {product_skus}
all_product_images = {{}}

for sku in product_skus:
    # Mock product data for demo
    product_data = {{'sku': sku, 'name': f'Product {{sku}}', 'category': 'tools'}}
    images = visual_module._find_product_images(sku, product_data)
    all_product_images[sku] = images

print(f"Found images for {{len(all_product_images)}} products")
result = all_product_images
""",
            "requirements": ["opencv-python", "pillow"]
        })
        
        # Step 2: Analyze images
        workflow.add_node("PythonCodeNode", "analyze_images", {
            "code": """
from visual_understanding import AnalysisType, ImageType

analysis_results = {}

for sku, image_paths in all_product_images.items():
    product_analyses = []
    
    for image_path in image_paths[:3]:  # Limit to 3 images per product
        if Path(image_path).exists():
            analysis = visual_module.analyze_image(
                image_path,
                ImageType.PRODUCT_PHOTO,
                [AnalysisType.OBJECT_DETECTION, AnalysisType.TEXT_EXTRACTION, 
                 AnalysisType.SAFETY_ANALYSIS, AnalysisType.TOOL_RECOGNITION]
            )
            product_analyses.append(analysis.to_dict())
    
    analysis_results[sku] = product_analyses

print(f"Analyzed images for {len(analysis_results)} products")
result = analysis_results
""",
            "requirements": []
        })
        
        # Step 3: Generate enhanced product data
        workflow.add_node("PythonCodeNode", "enhance_products", {
            "code": """
enhanced_products = []

for sku, analyses in analysis_results.items():
    # Mock product data
    product_data = {'sku': sku, 'name': f'Product {sku}', 'category': 'tools'}
    
    # Get image paths for this product
    image_paths = all_product_images.get(sku, [])
    
    # Enhance with visual knowledge
    enhanced = visual_module.enhance_product_with_visual_knowledge(
        sku, product_data, image_paths
    )
    
    enhanced_products.append(enhanced)

print(f"Enhanced {len(enhanced_products)} products with visual analysis")
result = enhanced_products
""",
            "requirements": []
        })
        
        # Step 4: Save results
        workflow.add_node("PythonCodeNode", "save_results", {
            "code": """
import json
from datetime import datetime

output_file = f'visual_enhanced_products_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

with open(output_file, 'w') as f:
    json.dump(enhanced_products, f, indent=2, default=str)

print(f"Visual enhancement results saved to {output_file}")
result = output_file
""",
            "requirements": []
        })
        
        # Connect workflow
        workflow.connect("find_images", "analyze_images")
        workflow.connect("analyze_images", "enhance_products")
        workflow.connect("enhance_products", "save_results")
        
        return workflow


# Example usage and testing functions
def create_sample_visual_module() -> VisualUnderstandingModule:
    """Create a sample visual understanding module for testing."""
    config = VisualAnalysisConfig(
        use_ai_models=False,  # Disable for basic testing
        enable_ocr=False,     # Disable if tesseract not available
        save_annotated_images=True
    )
    return VisualUnderstandingModule(config)


def demonstrate_visual_enhancement():
    """Demonstrate how visual analysis enhances basic product data."""
    print("=== Visual Understanding Module Demo ===\\n")
    
    # Create visual module
    visual_module = create_sample_visual_module()
    
    # Sample basic product data
    basic_product = {
        "sku": "drill-cordless-18v",
        "name": "18V Cordless Drill",
        "price": 89.99,
        "category": "power tools",
        "description": "Cordless drill with 18V battery"
    }
    
    print(f"BASIC PRODUCT: {basic_product['name']} (${basic_product['price']})")
    print(f"Category: {basic_product['category']}")
    print(f"Description: {basic_product['description']}")
    print()
    
    # For demo purposes, we'll simulate having product images
    # In reality, these would be actual image files
    print("VISUAL ANALYSIS CAPABILITIES:")
    print("  • Object Detection - Identify tools and components in images")
    print("  • Text Extraction - Read labels, measurements, and instructions")
    print("  • Safety Analysis - Detect potential hazards and safety equipment")
    print("  • Tool Recognition - Identify specific tools and their usage contexts")
    print("  • Assembly Sequence - Extract step-by-step instructions from images")
    print("  • Measurement Extraction - Read dimensions and specifications")
    print()
    
    print("ENHANCED PRODUCT CAPABILITIES:")
    print("  • Visual usage contexts from installation guides")
    print("  • Safety recommendations from hazard analysis")
    print("  • Tool compatibility identification")
    print("  • Assembly difficulty assessment")
    print("  • Visual quality metrics for product images")
    print("  • Measurement specifications from technical drawings")
    print()
    
    # Simulate enhanced data structure
    enhanced_data = {
        "visual_analysis": {
            "status": "demo_mode",
            "capabilities": [
                "object_detection",
                "text_extraction",
                "safety_analysis",
                "tool_recognition",
                "measurement_extraction"
            ]
        },
        "tool_usage_visual": {
            "identified_in_images": ["drill", "drill_bits", "battery"],
            "usage_contexts": ["assembly", "installation", "maintenance"]
        },
        "safety_visual_analysis": {
            "recommended_safety_gear": ["safety_glasses", "work_gloves"],
            "hazard_warnings": ["rotating_parts", "electrical_components"],
            "safety_score": 0.85
        },
        "assembly_visual_guide": {
            "has_visual_instructions": True,
            "complexity_level": "intermediate",
            "estimated_assembly_time": "15 minutes"
        },
        "measurement_specifications": {
            "dimensions_from_images": True,
            "technical_drawings_available": False,
            "measurement_accuracy": "high"
        },
        "visual_quality_assessment": {
            "image_quality_score": 0.78,
            "analysis_confidence": 0.82,
            "completeness": 0.75,
            "recommendations": ["Add technical diagram", "Include measurement reference"]
        }
    }
    
    basic_product.update(enhanced_data)
    
    print("SAMPLE ENHANCED DATA STRUCTURE:")
    for key, value in enhanced_data.items():
        print(f"  {key}:")
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                print(f"    {subkey}: {subvalue}")
        else:
            print(f"    {value}")
        print()


if __name__ == "__main__":
    # Run demonstration
    demonstrate_visual_enhancement()