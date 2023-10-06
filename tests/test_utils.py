from app.utils import validate_date


def test_validate_date():
    assert validate_date("01/10/2023") == True
    assert validate_date("32/12/2023") == False
    assert validate_date("01/13/2023") == False
    assert validate_date("01/10/3000") == False
    assert validate_date("random_string") == False
