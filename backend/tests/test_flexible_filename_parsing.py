"""Test flexible filename parsing functionality"""

import pytest
from app.utils import parse_filename


def test_strict_format_still_works():
    """Test that the original strict format still works"""
    year, cw_label, category_raw, category = parse_filename("2025_CW01_DEV.docx")
    assert year == 2025
    assert cw_label == "CW01"
    assert category_raw == "DEV"
    assert category == "Development"
    
    year, cw_label, category_raw, category = parse_filename("2024_CW16_EPC.docx")
    assert year == 2024
    assert cw_label == "CW16"
    assert category_raw == "EPC"
    assert category == "EPC"


def test_flexible_format_with_spaces():
    """Test flexible format with spaces and dashes"""
    year, cw_label, category_raw, category = parse_filename("Weekly Report_CW16 - DEV.docx")
    assert cw_label == "CW16"
    assert category_raw == "DEV"
    assert category == "Development"
    
    year, cw_label, category_raw, category = parse_filename("Report CW01 EPC.docx")
    assert cw_label == "CW01"
    assert category_raw == "EPC"
    assert category == "EPC"


def test_flexible_format_different_order():
    """Test that order doesn't matter"""
    year, cw_label, category_raw, category = parse_filename("DEV Report CW02.docx")
    assert cw_label == "CW02"
    assert category_raw == "DEV"
    assert category == "Development"
    
    year, cw_label, category_raw, category = parse_filename("FINANCE CW10 Weekly Update.docx")
    assert cw_label == "CW10"
    assert category_raw == "FINANCE"
    assert category == "Finance"


def test_category_variations():
    """Test different category name variations"""
    # Development variations
    year, cw_label, category_raw, category = parse_filename("CW01 Development Report.docx")
    assert category_raw == "DEV"
    assert category == "Development"
    
    # Finance variations
    year, cw_label, category_raw, category = parse_filename("CW02 Financial Report.docx")
    assert category_raw == "FINANCE"
    assert category == "Finance"
    
    year, cw_label, category_raw, category = parse_filename("CW03 FIN Update.docx")
    assert category_raw == "FINANCE"
    assert category == "Finance"
    
    # Investment variations
    year, cw_label, category_raw, category = parse_filename("CW04 Investment Analysis.docx")
    assert category_raw == "INVESTMENT"
    assert category == "Investment"
    
    year, cw_label, category_raw, category = parse_filename("CW05 INVEST Report.docx")
    assert category_raw == "INVESTMENT"
    assert category == "Investment"


def test_single_digit_cw():
    """Test single digit CW numbers are properly formatted"""
    year, cw_label, category_raw, category = parse_filename("CW1 DEV Report.docx")
    assert cw_label == "CW01"  # Should be zero-padded
    
    year, cw_label, category_raw, category = parse_filename("CW9 EPC Update.docx")
    assert cw_label == "CW09"  # Should be zero-padded


def test_year_extraction():
    """Test year extraction from various positions"""
    year, cw_label, category_raw, category = parse_filename("2025 CW01 DEV Report.docx")
    assert year == 2025
    
    year, cw_label, category_raw, category = parse_filename("CW02 EPC Report 2024.docx")
    assert year == 2024
    
    year, cw_label, category_raw, category = parse_filename("Weekly Report CW03 DEV 2023.docx")
    assert year == 2023


def test_year_defaults_to_current():
    """Test that year defaults to current year if not found"""
    from datetime import datetime
    current_year = datetime.now().year
    
    year, cw_label, category_raw, category = parse_filename("CW01 DEV Report.docx")
    assert year == current_year


def test_case_insensitive():
    """Test that parsing is case insensitive"""
    year, cw_label, category_raw, category = parse_filename("cw01 dev report.docx")
    assert cw_label == "CW01"
    assert category_raw == "DEV"
    assert category == "Development"
    
    year, cw_label, category_raw, category = parse_filename("Weekly Report_cw16 - epc.DOCX")
    assert cw_label == "CW16"
    assert category_raw == "EPC"
    assert category == "EPC"


def test_missing_cw_raises_error():
    """Test that missing CW raises appropriate error"""
    with pytest.raises(ValueError, match="No calendar week"):
        parse_filename("DEV Report 2025.docx")
    
    with pytest.raises(ValueError, match="No calendar week"):
        parse_filename("Weekly Report EPC.docx")


def test_missing_category_raises_error():
    """Test that missing category raises appropriate error"""
    with pytest.raises(ValueError, match="No valid category"):
        parse_filename("CW01 Report.docx")
    
    with pytest.raises(ValueError, match="No valid category"):
        parse_filename("Weekly Report CW16.docx")


def test_invalid_category_raises_error():
    """Test that invalid categories raise error"""
    with pytest.raises(ValueError, match="No valid category"):
        parse_filename("CW01 INVALID Report.docx")
    
    with pytest.raises(ValueError, match="No valid category"):
        parse_filename("CW02 MARKETING Update.docx")


def test_complex_filenames():
    """Test more complex real-world filename examples"""
    year, cw_label, category_raw, category = parse_filename("Q-Energy Weekly Report_CW16 - DEV Team Update.docx")
    assert cw_label == "CW16"
    assert category_raw == "DEV"
    assert category == "Development"
    
    year, cw_label, category_raw, category = parse_filename("2025_Q1_CW05_FINANCE_Quarterly_Review.docx")
    assert year == 2025
    assert cw_label == "CW05"
    assert category_raw == "FINANCE"
    assert category == "Finance"
    
    year, cw_label, category_raw, category = parse_filename("Project Status - CW12 - EPC Division - 2024.docx")
    assert year == 2024
    assert cw_label == "CW12"
    assert category_raw == "EPC"
    assert category == "EPC"


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    # Very long filename
    long_name = "Very_Long_Project_Name_With_Many_Details_And_Information_CW25_INVESTMENT_Report_Final_Version_2025.docx"
    year, cw_label, category_raw, category = parse_filename(long_name)
    assert year == 2025
    assert cw_label == "CW25"
    assert category_raw == "INVESTMENT"
    assert category == "Investment"
    
    # Multiple years (should pick one of the valid years)
    year, cw_label, category_raw, category = parse_filename("2023_Archive_2024_CW01_DEV_Report_2025.docx")
    assert year in [2023, 2024, 2025]  # Any valid year is acceptable
    assert cw_label == "CW01"
    
    # Multiple CW numbers (should pick the first one)
    year, cw_label, category_raw, category = parse_filename("CW01_vs_CW02_Comparison_DEV_Report.docx")
    assert cw_label == "CW01"  # First CW found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
