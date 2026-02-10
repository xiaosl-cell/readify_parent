"""
Sentence-BERT service for computing sentence similarity
"""
import os
import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SentenceBertService:
    """
    Sentence-BERT 服务类，用于计算句子相似度
    """
    
    _instance = None
    _model = None
    _model_path = None
    
    def __new__(cls, model_path: Optional[str] = None):
        """
        单例模式，确保模型只加载一次
        
        Args:
            model_path: 模型权重路径
        """
        if cls._instance is None:
            cls._instance = super(SentenceBertService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化 Sentence-BERT 服务
        
        Args:
            model_path: 模型权重路径，默认使用项目中的本地模型
        """
        # 如果已经初始化过且路径相同，直接返回
        if self._model is not None and self._model_path == model_path:
            return
        
        # 设置默认模型路径
        if model_path is None:
            # 使用项目中的本地模型路径
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            model_path = os.path.join(current_dir, "model_weights", "paraphrase-multilingual-MiniLM-L12-v2")
        
        self._model_path = model_path
        self._load_model()
    
    def _load_model(self):
        """
        加载 Sentence-BERT 模型
        """
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading Sentence-BERT model from: {self._model_path}")
            
            # 加载本地模型，强制使用CPU
            self._model = SentenceTransformer(self._model_path, device='cpu')
            
            logger.info("Sentence-BERT model loaded successfully")
            
        except ImportError as e:
            logger.error("sentence-transformers library not installed. Please install it using: pip install sentence-transformers")
            raise ImportError(
                "sentence-transformers library is required. "
                "Install it using: pip install sentence-transformers"
            ) from e
        except Exception as e:
            logger.error(f"Failed to load Sentence-BERT model: {str(e)}")
            raise RuntimeError(f"Failed to load Sentence-BERT model: {str(e)}") from e
    
    def encode(self, sentences: List[str], batch_size: int = 32) -> np.ndarray:
        """
        将句子编码为向量
        
        Args:
            sentences: 句子列表
            batch_size: 批处理大小
            
        Returns:
            句子向量数组
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Please initialize the service first.")
        
        try:
            embeddings = self._model.encode(
                sentences,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"Failed to encode sentences: {str(e)}")
            raise RuntimeError(f"Failed to encode sentences: {str(e)}") from e
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本之间的余弦相似度
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            
        Returns:
            相似度分数（0-1之间）
        """
        if not text1 or not text2:
            # 如果有任一文本为空，返回0相似度
            return 0.0
        
        try:
            # 编码两个句子
            embeddings = self.encode([text1, text2])
            
            # 计算余弦相似度
            from sentence_transformers import util
            similarity = util.cos_sim(embeddings[0], embeddings[1])
            
            # 转换为float并确保在0-1范围内
            score = float(similarity.item())
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Failed to compute similarity: {str(e)}")
            raise RuntimeError(f"Failed to compute similarity: {str(e)}") from e
    
    def compute_batch_similarity(
        self,
        text_pairs: List[Tuple[str, str]],
        batch_size: int = 16
    ) -> List[float]:
        """
        批量计算文本对的相似度
        
        Args:
            text_pairs: 文本对列表 [(text1, text2), ...]
            batch_size: 批处理大小
            
        Returns:
            相似度分数列表
        """
        if not text_pairs:
            return []
        
        try:
            from sentence_transformers import util
            
            # 分离文本对
            texts1 = [pair[0] if pair[0] else "" for pair in text_pairs]
            texts2 = [pair[1] if pair[1] else "" for pair in text_pairs]
            
            # 批量编码
            embeddings1 = self.encode(texts1, batch_size=batch_size)
            embeddings2 = self.encode(texts2, batch_size=batch_size)
            
            # 计算相似度
            similarities = []
            for emb1, emb2, (t1, t2) in zip(embeddings1, embeddings2, text_pairs):
                # 如果有任一文本为空，相似度为0
                if not t1 or not t2:
                    similarities.append(0.0)
                else:
                    sim = util.cos_sim(emb1, emb2)
                    score = float(sim.item())
                    similarities.append(max(0.0, min(1.0, score)))
            
            return similarities
            
        except Exception as e:
            logger.error(f"Failed to compute batch similarity: {str(e)}")
            raise RuntimeError(f"Failed to compute batch similarity: {str(e)}") from e
    
    def is_model_loaded(self) -> bool:
        """
        检查模型是否已加载
        
        Returns:
            是否已加载
        """
        return self._model is not None
    
    def get_model_info(self) -> dict:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "model_loaded": self.is_model_loaded(),
            "model_path": self._model_path,
            "device": "cpu"
        }


# 全局单例实例
_sentence_bert_service = None


def get_sentence_bert_service(model_path: Optional[str] = None) -> SentenceBertService:
    """
    获取 Sentence-BERT 服务实例（单例）
    
    Args:
        model_path: 模型权重路径
        
    Returns:
        SentenceBertService 实例
    """
    global _sentence_bert_service
    if _sentence_bert_service is None:
        _sentence_bert_service = SentenceBertService(model_path)
    return _sentence_bert_service

