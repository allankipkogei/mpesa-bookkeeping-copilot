"""
AI-powered transaction categorization system.
Uses pattern matching and keyword analysis to automatically classify M-Pesa transactions.
"""

import re
from typing import Dict, List, Optional, Any


class TransactionCategorizer:
    """Intelligent transaction categorization using pattern matching and keywords"""
    
    # Category definitions with keywords and patterns
    CATEGORIES = {
        "Food": {
            "keywords": [
                "restaurant", "cafe", "coffee", "pizza", "burger", "chicken", 
                "food", "meal", "breakfast", "lunch", "dinner", "snack",
                "bakery", "grocery", "supermarket", "shop", "store",
                "kfc", "subway", "dominos", "java", "artcaffe", "naivas",
                "carrefour", "quickmart", "chandarana", "tuskys", "nakumatt"
            ],
            "patterns": [
                r"restaurant|cafe|coffee|pizza|burger|chicken|food|meal",
                r"bakery|grocery|supermarket|kfc|subway"
            ]
        },
        "Transport": {
            "keywords": [
                "uber", "taxi", "matatu", "bus", "fuel", "petrol", "diesel",
                "parking", "toll", "transport", "travel", "fare", "ride",
                "bolt", "little", "grab", "total", "shell", "kenol", "ola"
            ],
            "patterns": [
                r"uber|taxi|matatu|bus|fuel|petrol|diesel",
                r"parking|toll|transport|travel|bolt|little"
            ]
        },
        "Inventory": {
            "keywords": [
                "stock", "inventory", "wholesale", "supplier", "goods",
                "merchandise", "supply", "warehouse", "purchase order",
                "bulk", "vendor", "procurement", "raw material"
            ],
            "patterns": [
                r"stock|inventory|wholesale|supplier",
                r"goods|merchandise|supply|warehouse"
            ]
        },
        "Personal": {
            "keywords": [
                "personal", "self", "family", "clothing", "clothes", "shoes",
                "entertainment", "movie", "cinema", "gym", "fitness", "salon",
                "beauty", "haircut", "spa", "gift", "shopping", "fashion"
            ],
            "patterns": [
                r"personal|clothing|clothes|shoes|entertainment",
                r"movie|cinema|gym|fitness|salon|beauty"
            ]
        },
        "Utilities": {
            "keywords": [
                "kplc", "electricity", "power", "water", "nairobi water",
                "internet", "wifi", "safaricom", "airtel", "telkom",
                "rent", "landlord", "utility", "bill", "garbage", "sewage"
            ],
            "patterns": [
                r"kplc|electricity|power|water",
                r"internet|wifi|safaricom|airtel|telkom|rent|utility"
            ]
        },
        "Business Expenses": {
            "keywords": [
                "office", "stationery", "printing", "business", "marketing",
                "advertising", "license", "permit", "registration", "legal",
                "accounting", "consultant", "software", "subscription",
                "meeting", "conference", "training", "professional"
            ],
            "patterns": [
                r"office|stationery|printing|business|marketing",
                r"advertising|license|permit|consultant|software"
            ]
        }
    }
    
    # Transaction type indicators
    EXPENSE_TYPES = ["B2C", "PAYBILL", "BUYGOODS", "P2P"]
    INCOME_TYPES = ["C2B"]
    
    @classmethod
    def categorize(cls, description: str, trans_type: str, phone_number: str = "", 
                   amount: float = 0) -> Dict[str, Any]:
        """
        Categorize a transaction based on description, type, and other attributes.
        
        Args:
            description: Transaction description or details
            trans_type: Transaction type (C2B, B2C, etc.)
            phone_number: Associated phone number
            amount: Transaction amount
            
        Returns:
            Dict with category, confidence, and reasoning
        """
        if not description:
            return cls._default_category(trans_type)
        
        # Normalize description for matching
        desc_lower = description.lower()
        
        # Score each category
        category_scores = {}
        for category, config in cls.CATEGORIES.items():
            score = cls._calculate_score(desc_lower, config)
            if score > 0:
                category_scores[category] = score
        
        # If no matches, use transaction type to determine category
        if not category_scores:
            return cls._default_category(trans_type)
        
        # Get highest scoring category
        best_category = max(category_scores.items(), key=lambda x: x[1])
        category_name = best_category[0]
        confidence = min(best_category[1] / 10.0, 1.0)  # Normalize to 0-1
        
        # Income transactions should not be categorized as expenses
        if trans_type in cls.INCOME_TYPES and category_name != "Business Expenses":
            return {
                "category": "Income",
                "confidence": 1.0,
                "sub_category": category_name,
                "reasoning": f"Income from {category_name.lower()}"
            }
        
        return {
            "category": category_name,
            "confidence": confidence,
            "sub_category": None,
            "reasoning": f"Matched keywords in description"
        }
    
    @classmethod
    def _calculate_score(cls, description: str, config: Dict) -> int:
        """Calculate matching score for a category"""
        score = 0
        
        # Keyword matching (exact matches)
        for keyword in config["keywords"]:
            if keyword in description:
                score += 2
        
        # Pattern matching (regex)
        for pattern in config["patterns"]:
            if re.search(pattern, description, re.IGNORECASE):
                score += 3
        
        return score
    
    @classmethod
    def _default_category(cls, trans_type: str) -> Dict[str, Any]:
        """Return default category based on transaction type"""
        if trans_type in cls.INCOME_TYPES:
            return {
                "category": "Income",
                "confidence": 0.8,
                "sub_category": None,
                "reasoning": "Money received (C2B transaction)"
            }
        elif trans_type in cls.EXPENSE_TYPES:
            return {
                "category": "Uncategorized",
                "confidence": 0.5,
                "sub_category": None,
                "reasoning": "No matching keywords found"
            }
        else:
            return {
                "category": "Other",
                "confidence": 0.5,
                "sub_category": None,
                "reasoning": "Unknown transaction type"
            }
    
    @classmethod
    def bulk_categorize(cls, transactions: List[Dict]) -> List[Dict]:
        """
        Categorize multiple transactions at once.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of transactions with added categorization data
        """
        categorized = []
        for tx in transactions:
            result = cls.categorize(
                description=tx.get("description", ""),
                trans_type=tx.get("trans_type", ""),
                phone_number=tx.get("phone_number", ""),
                amount=tx.get("amount", 0)
            )
            tx_copy = tx.copy()
            tx_copy.update(result)
            categorized.append(tx_copy)
        
        return categorized
    
    @classmethod
    def get_categories(cls) -> List[str]:
        """Get list of all available categories"""
        return list(cls.CATEGORIES.keys()) + ["Income", "Uncategorized", "Other"]
    
    @classmethod
    def suggest_category(cls, description: str) -> List[Dict[str, Any]]:
        """
        Get top 3 category suggestions for a description.
        
        Args:
            description: Transaction description
            
        Returns:
            List of top 3 categories with confidence scores
        """
        if not description:
            return []
        
        desc_lower = description.lower()
        category_scores = {}
        
        for category, config in cls.CATEGORIES.items():
            score = cls._calculate_score(desc_lower, config)
            if score > 0:
                category_scores[category] = score
        
        # Sort by score and get top 3
        sorted_categories = sorted(
            category_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        return [
            {
                "category": cat,
                "confidence": min(score / 10.0, 1.0),
                "score": score
            }
            for cat, score in sorted_categories
        ]
