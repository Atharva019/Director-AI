from config import Settings


def test_cors_regex_disabled_in_production():
    s = Settings(APP_ENV="production", CORS_ORIGINS="https://app.example.com")
    assert s.cors_origin_list == ["https://app.example.com"]
    assert s.is_production is True


def test_cors_regex_flag_in_development():
    s = Settings(APP_ENV="development")
    assert s.is_production is False


def test_free_plan_limits_present():
    s = Settings()
    assert s.plan_free_analyses == 5
    assert s.plan_free_projects == 2
