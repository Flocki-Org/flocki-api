from src.app.users.services.passwordUtil import PasswordUtil


def test_hash_pwd_returns_bcrypt_hash_string():
    password_util = PasswordUtil()
    hashed = password_util.hash_pwd("secret-password")

    assert isinstance(hashed, str)
    assert hashed != "secret-password"
    assert hashed.startswith("$2")


def test_hash_pwd_accepts_bytes():
    password_util = PasswordUtil()
    hashed = password_util.hash_pwd(b"secret-password")

    assert password_util.verify_pwd("secret-password", hashed) is True


def test_verify_pwd_true_for_matching_password():
    password_util = PasswordUtil()
    hashed = password_util.hash_pwd("correct-horse")

    assert password_util.verify_pwd("correct-horse", hashed) is True


def test_verify_pwd_false_for_wrong_password():
    password_util = PasswordUtil()
    hashed = password_util.hash_pwd("correct-horse")

    assert password_util.verify_pwd("wrong-password", hashed) is False


def test_verify_pwd_accepts_string_hash():
    password_util = PasswordUtil()
    hashed = password_util.hash_pwd("abc")

    assert password_util.verify_pwd("abc", hashed) is True
