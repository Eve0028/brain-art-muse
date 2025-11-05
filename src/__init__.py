"""
Brain Art - Interactive EEG Visualization
Main package with application modules
"""

__version__ = "1.0.0"
__author__ = "Brain Art Team"

from .muse_connector import MuseConnector
from .eeg_processor import EEGProcessor
from .brain_visualizer import BrainVisualizer
from .eeg_visualizer import EEGVisualizer, SimpleEEGVisualizer, create_eeg_visualizer
from .signal_quality import SignalQualityChecker, quick_quality_check

__all__ = [
    'MuseConnector',
    'EEGProcessor',
    'BrainVisualizer',
    'EEGVisualizer',
    'SimpleEEGVisualizer',
    'create_eeg_visualizer',
    'SignalQualityChecker',
    'quick_quality_check',
]
