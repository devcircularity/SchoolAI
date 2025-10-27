# app/services/ollama_service/regex_validator.py - Regex validation and testing functionality

import re
from typing import Dict, Any, List
from .base import OllamaBaseService


class OllamaRegexValidator(OllamaBaseService):
    """Regex validation, testing, and improvement functionality"""
    
    def _validate_regex_comprehensive(self, regex: str, test_phrases: List[str]) -> Dict[str, Any]:
        """Comprehensive validation of the generated regex against input phrases"""
        
        errors = []
        matches = []
        confidence = 0.0
        detailed_results = []
        
        if not regex:
            return {
                "confidence": 0.0,
                "errors": ["Empty regex pattern generated"],
                "test_matches": [],
                "detailed_results": []
            }
        
        try:
            # Test compile the regex
            compiled_regex = re.compile(regex, re.IGNORECASE)
            
            # Test against input phrases
            successful_matches = 0
            failed_phrases = []
            
            for phrase in test_phrases:
                try:
                    match = compiled_regex.search(phrase)
                    if match:
                        matches.append(phrase)
                        successful_matches += 1
                        detailed_results.append({
                            "phrase": phrase,
                            "matched": True,
                            "match_text": match.group(0),
                            "start": match.start(),
                            "end": match.end()
                        })
                    else:
                        failed_phrases.append(phrase)
                        detailed_results.append({
                            "phrase": phrase,
                            "matched": False,
                            "reason": "No match found"
                        })
                except Exception as e:
                    failed_phrases.append(phrase)
                    detailed_results.append({
                        "phrase": phrase,
                        "matched": False,
                        "reason": f"Match error: {str(e)}"
                    })
            
            # Calculate confidence based on match rate with more nuanced scoring
            if test_phrases:
                match_rate = successful_matches / len(test_phrases)
                
                if match_rate >= 0.9:
                    confidence = 0.95  # Excellent
                elif match_rate >= 0.8:
                    confidence = 0.85  # Very good
                elif match_rate >= 0.7:
                    confidence = 0.75  # Good
                elif match_rate >= 0.5:
                    confidence = 0.6   # Acceptable
                elif match_rate >= 0.3:
                    confidence = 0.4   # Poor but usable
                else:
                    confidence = 0.2   # Very poor
                
                # Add detailed error messages for failed matches
                if failed_phrases:
                    errors.append(f"Failed to match {len(failed_phrases)}/{len(test_phrases)} phrases:")
                    for phrase in failed_phrases[:3]:  # Show first 3 failed phrases
                        errors.append(f"  - '{phrase}'")
                    if len(failed_phrases) > 3:
                        errors.append(f"  - ...and {len(failed_phrases) - 3} more phrases")
            
            # Additional validation checks
            if len(regex) < 5:
                errors.append("Pattern is very simple - may be too restrictive")
                confidence *= 0.7
            elif len(regex) < 15:
                errors.append("Pattern seems simple - consider if it's flexible enough")
                confidence *= 0.9
            
            if len(regex) > 300:
                errors.append("Pattern is very complex - may be over-engineered")
                confidence *= 0.8
            elif len(regex) > 150:
                errors.append("Pattern is quite complex - verify it's not overfitted")
                confidence *= 0.95
            
            # Check for balanced parentheses
            if regex.count('(') != regex.count(')'):
                errors.append("Unbalanced parentheses in regex")
                confidence = 0.0
            
            # Check for good flexibility indicators
            flexibility_indicators = ['?', '|', '*', '+']
            if not any(indicator in regex for indicator in flexibility_indicators):
                errors.append("Pattern lacks flexibility indicators - may be too rigid")
                confidence *= 0.8
            
            # Check for word boundaries
            if '\\b' not in regex:
                errors.append("Pattern lacks word boundaries - may have false positives")
                confidence *= 0.9
            
            # Provide improvement suggestions
            if match_rate < 0.8 and len(test_phrases) > 1:
                errors.append("Consider making the pattern more flexible for natural language variations")
                
        except re.error as e:
            errors.append(f"Invalid regex syntax: {str(e)}")
            confidence = 0.0
        except Exception as e:
            errors.append(f"Regex validation error: {str(e)}")
            confidence = 0.0
        
        return {
            "confidence": confidence,
            "errors": errors,
            "test_matches": matches,
            "detailed_results": detailed_results,
            "match_rate": successful_matches / len(test_phrases) if test_phrases else 0
        }
    
    async def test_regex_against_phrases(self, regex: str, test_phrases: List[str]) -> Dict[str, Any]:
        """Test a regex pattern against a list of phrases with detailed results"""
        
        results = {
            "regex": regex,
            "matches": [],
            "non_matches": [],
            "errors": [],
            "summary": {
                "total_tested": len(test_phrases),
                "successful_matches": 0,
                "failed_matches": 0,
                "match_rate": 0.0
            }
        }
        
        if not regex:
            results["errors"].append("No regex pattern provided")
            return results
        
        try:
            compiled_regex = re.compile(regex, re.IGNORECASE)
            
            for phrase in test_phrases:
                try:
                    match = compiled_regex.search(phrase)
                    if match:
                        results["matches"].append({
                            "phrase": phrase,
                            "match_text": match.group(0),
                            "start": match.start(),
                            "end": match.end(),
                            "groups": match.groups() if match.groups() else None
                        })
                        results["summary"]["successful_matches"] += 1
                    else:
                        results["non_matches"].append(phrase)
                        results["summary"]["failed_matches"] += 1
                except Exception as e:
                    results["non_matches"].append(phrase)
                    results["summary"]["failed_matches"] += 1
                    results["errors"].append(f"Error testing phrase '{phrase}': {str(e)}")
            
            # Calculate match rate
            if test_phrases:
                results["summary"]["match_rate"] = results["summary"]["successful_matches"] / len(test_phrases)
                    
        except re.error as e:
            results["errors"].append(f"Regex compilation error: {str(e)}")
        except Exception as e:
            results["errors"].append(f"Testing error: {str(e)}")
        
        return results
    
    async def analyze_regex_performance(
        self, 
        regex: str, 
        positive_phrases: List[str],
        negative_phrases: List[str] = None
    ) -> Dict[str, Any]:
        """Analyze regex performance against positive and negative test cases"""
        
        negative_phrases = negative_phrases or []
        
        analysis = {
            "regex": regex,
            "positive_test_results": {},
            "negative_test_results": {},
            "overall_performance": {},
            "recommendations": []
        }
        
        try:
            # Test against positive phrases (should match)
            if positive_phrases:
                positive_results = await self.test_regex_against_phrases(regex, positive_phrases)
                analysis["positive_test_results"] = positive_results
                
                positive_match_rate = positive_results["summary"]["match_rate"]
                analysis["overall_performance"]["positive_match_rate"] = positive_match_rate
            
            # Test against negative phrases (should NOT match)
            if negative_phrases:
                negative_results = await self.test_regex_against_phrases(regex, negative_phrases)
                analysis["negative_test_results"] = negative_results
                
                # For negative tests, we want a LOW match rate (few false positives)
                negative_match_rate = negative_results["summary"]["match_rate"]
                false_positive_rate = negative_match_rate
                analysis["overall_performance"]["false_positive_rate"] = false_positive_rate
                analysis["overall_performance"]["negative_accuracy"] = 1.0 - false_positive_rate
            
            # Calculate overall score
            positive_score = analysis["overall_performance"].get("positive_match_rate", 0)
            negative_score = analysis["overall_performance"].get("negative_accuracy", 1.0)
            
            # Weighted average (positive matching is more important)
            overall_score = (positive_score * 0.7) + (negative_score * 0.3)
            analysis["overall_performance"]["overall_score"] = overall_score
            
            # Generate recommendations
            recommendations = []
            
            if positive_score < 0.7:
                recommendations.append("Consider making the pattern more flexible to capture more positive cases")
            elif positive_score < 0.5:
                recommendations.append("Pattern is too restrictive - major improvements needed for positive matching")
            
            if negative_score < 0.8:
                recommendations.append("Pattern may be too broad - consider adding restrictions to reduce false positives")
            elif negative_score < 0.6:
                recommendations.append("Pattern has high false positive rate - needs more precision")
            
            if overall_score >= 0.9:
                recommendations.append("Excellent pattern performance!")
            elif overall_score >= 0.8:
                recommendations.append("Good pattern performance with minor room for improvement")
            elif overall_score >= 0.6:
                recommendations.append("Moderate pattern performance - consider refinements")
            else:
                recommendations.append("Pattern needs significant improvement")
            
            analysis["recommendations"] = recommendations
            
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis