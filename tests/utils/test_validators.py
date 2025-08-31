"""Tests for utils.validators module."""

import pytest

from src.playwright_search.utils.validators import ValidationError, InputValidator


class TestInputValidator:
    """Tests for InputValidator class."""
    
    def test_validate_engine_valid(self):
        """Test validate_engine with valid engines."""
        assert InputValidator.validate_engine("google") == "google"
        assert InputValidator.validate_engine("GOOGLE") == "google"
        assert InputValidator.validate_engine("bing") == "bing"
        assert InputValidator.validate_engine("duckduckgo") == "duckduckgo"
        assert InputValidator.validate_engine("ddg") == "duckduckgo"  # alias
    
    def test_validate_engine_invalid(self):
        """Test validate_engine with invalid engines."""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_engine("invalid_engine")
        assert "Invalid engine" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            InputValidator.validate_engine("")
        
        with pytest.raises(ValidationError):
            InputValidator.validate_engine(None)
    
    def test_validate_engines_valid(self):
        """Test validate_engines with valid engine lists."""
        result = InputValidator.validate_engines(["google", "bing"])
        assert set(result) == {"google", "bing"}
        
        # Test deduplication
        result = InputValidator.validate_engines(["google", "google", "bing"])
        assert set(result) == {"google", "bing"}
        
        # Test with aliases
        result = InputValidator.validate_engines(["ddg", "duckduckgo"])
        assert result == ["duckduckgo"]  # Should deduplicate aliases
    
    def test_validate_engines_invalid(self):
        """Test validate_engines with invalid inputs."""
        with pytest.raises(ValidationError):
            InputValidator.validate_engines([])
        
        with pytest.raises(ValidationError):
            InputValidator.validate_engines(["google", "invalid"])
    
    def test_validate_timeout_valid(self):
        """Test validate_timeout with valid values."""
        assert InputValidator.validate_timeout(5000) == 5000
        assert InputValidator.validate_timeout(30000) == 30000
        assert InputValidator.validate_timeout(300000) == 300000
    
    def test_validate_timeout_invalid(self):
        """Test validate_timeout with invalid values."""
        with pytest.raises(ValidationError):
            InputValidator.validate_timeout(500)  # Too small
        
        with pytest.raises(ValidationError):
            InputValidator.validate_timeout(400000)  # Too large
        
        with pytest.raises(ValidationError):
            InputValidator.validate_timeout("30000")  # Wrong type
        
        with pytest.raises(ValidationError):
            InputValidator.validate_timeout(-1000)  # Negative
    
    def test_validate_concurrent_limit_valid(self):
        """Test validate_concurrent_limit with valid values."""
        assert InputValidator.validate_concurrent_limit(1) == 1
        assert InputValidator.validate_concurrent_limit(5) == 5
        assert InputValidator.validate_concurrent_limit(20) == 20
    
    def test_validate_concurrent_limit_invalid(self):
        """Test validate_concurrent_limit with invalid values."""
        with pytest.raises(ValidationError):
            InputValidator.validate_concurrent_limit(0)
        
        with pytest.raises(ValidationError):
            InputValidator.validate_concurrent_limit(25)  # Too large
        
        with pytest.raises(ValidationError):
            InputValidator.validate_concurrent_limit("5")  # Wrong type
    
    def test_validate_num_results_valid(self):
        """Test validate_num_results with valid values."""
        assert InputValidator.validate_num_results(1) == 1
        assert InputValidator.validate_num_results(10) == 10
        assert InputValidator.validate_num_results(100) == 100
    
    def test_validate_num_results_invalid(self):
        """Test validate_num_results with invalid values."""
        with pytest.raises(ValidationError):
            InputValidator.validate_num_results(0)
        
        with pytest.raises(ValidationError):
            InputValidator.validate_num_results(-1)
        
        with pytest.raises(ValidationError):
            InputValidator.validate_num_results(150)  # Too large
        
        with pytest.raises(ValidationError):
            InputValidator.validate_num_results("10")  # Wrong type
    
    def test_validate_months_valid(self):
        """Test validate_months with valid values."""
        assert InputValidator.validate_months(1) == 1
        assert InputValidator.validate_months(6) == 6
        assert InputValidator.validate_months(24) == 24
    
    def test_validate_months_invalid(self):
        """Test validate_months with invalid values."""
        with pytest.raises(ValidationError):
            InputValidator.validate_months(0)
        
        with pytest.raises(ValidationError):
            InputValidator.validate_months(25)  # Too large
        
        with pytest.raises(ValidationError):
            InputValidator.validate_months("6")  # Wrong type
    
    def test_validate_query_valid(self):
        """Test validate_query with valid queries."""
        assert InputValidator.validate_query("Python programming") == "Python programming"
        assert InputValidator.validate_query("  Machine learning  ") == "Machine learning"
        assert InputValidator.validate_query("A" * 1000) == "A" * 1000  # Max length
    
    def test_validate_query_invalid(self):
        """Test validate_query with invalid queries."""
        with pytest.raises(ValidationError):
            InputValidator.validate_query("")
        
        with pytest.raises(ValidationError):
            InputValidator.validate_query("   ")  # Only whitespace
        
        with pytest.raises(ValidationError):
            InputValidator.validate_query("A" * 1001)  # Too long
    
    def test_validate_keywords_valid(self):
        """Test validate_keywords with valid keyword lists."""
        result = InputValidator.validate_keywords(["Python", "Machine learning"])
        assert result == ["Python", "Machine learning"]
        
        # Test with whitespace cleanup
        result = InputValidator.validate_keywords(["  Python  ", "ML"])
        assert result == ["Python", "ML"]
    
    def test_validate_keywords_invalid(self):
        """Test validate_keywords with invalid keyword lists."""
        with pytest.raises(ValidationError):
            InputValidator.validate_keywords([])
        
        with pytest.raises(ValidationError):
            InputValidator.validate_keywords(["", "  ", ""])  # No valid keywords
    
    def test_validate_plan_type_valid(self):
        """Test validate_plan_type with valid plan types."""
        valid_types = ['technology', 'research', 'news', 'comparison', 'tutorial', 'comprehensive']
        
        for plan_type in valid_types:
            assert InputValidator.validate_plan_type(plan_type) == plan_type
    
    def test_validate_plan_type_invalid(self):
        """Test validate_plan_type with invalid plan types."""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_plan_type("invalid_type")
        assert "Invalid plan type" in str(exc_info.value)


class TestValidationError:
    """Tests for ValidationError exception."""
    
    def test_exception_creation(self):
        """Test ValidationError exception creation."""
        error = ValidationError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_exception_raising(self):
        """Test ValidationError exception raising."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Custom validation error")
        assert str(exc_info.value) == "Custom validation error"


if __name__ == "__main__":
    pytest.main([__file__])