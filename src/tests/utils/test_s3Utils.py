from unittest import mock

from botocore.exceptions import ClientError

from src.app.utils.s3Utils import S3Utils


@mock.patch("src.app.utils.s3Utils.boto3.resource")
def test_upload_file_success(mock_resource):
    mock_client = mock.Mock()
    mock_resource.return_value.meta.client = mock_client
    s3 = S3Utils(bucket_name="bucket", region="eu-west-1", access_key="ak", secret_access_key="sk")

    result = s3.upload_file(file=mock.Mock(), object_name="file.jpg")

    assert result is True
    mock_client.upload_fileobj.assert_called_once()


@mock.patch("src.app.utils.s3Utils.boto3.resource")
def test_upload_file_client_error_returns_false(mock_resource):
    mock_client = mock.Mock()
    mock_client.upload_fileobj.side_effect = ClientError({"Error": {"Code": "403", "Message": "Denied"}}, "Upload")
    mock_resource.return_value.meta.client = mock_client
    s3 = S3Utils(bucket_name="bucket")

    assert s3.upload_file(file=mock.Mock(), object_name="file.jpg") is False


@mock.patch("src.app.utils.s3Utils.boto3.resource")
def test_upload_file_generic_exception_returns_false(mock_resource):
    mock_client = mock.Mock()
    mock_client.upload_fileobj.side_effect = RuntimeError("boom")
    mock_resource.return_value.meta.client = mock_client
    s3 = S3Utils(bucket_name="bucket")

    assert s3.upload_file(file=mock.Mock(), object_name="file.jpg") is False


@mock.patch("src.app.utils.s3Utils.boto3.resource")
def test_get_file_returns_object(mock_resource):
    mock_obj = mock.Mock()
    mock_obj.get.return_value = {"Body": mock.Mock(), "Key": "file.jpg"}
    mock_resource.return_value.Object.return_value = mock_obj
    s3 = S3Utils(bucket_name="bucket")

    result = s3.get_file("file.jpg")

    assert result["Key"] == "file.jpg"
    mock_resource.return_value.Object.assert_called_once_with("bucket", key="file.jpg")


@mock.patch("src.app.utils.s3Utils.boto3.resource")
def test_get_file_reraises_exception(mock_resource):
    mock_obj = mock.Mock()
    mock_obj.get.side_effect = RuntimeError("missing")
    mock_resource.return_value.Object.return_value = mock_obj
    s3 = S3Utils(bucket_name="bucket")

    try:
        s3.get_file("missing.jpg")
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "missing"


@mock.patch("src.app.utils.s3Utils.boto3.resource")
def test_delete_file_success(mock_resource):
    mock_obj = mock.Mock()
    mock_resource.return_value.Object.return_value = mock_obj
    s3 = S3Utils(bucket_name="bucket")

    assert s3.delete_file("file.jpg") is True
    mock_obj.delete.assert_called_once()


@mock.patch("src.app.utils.s3Utils.boto3.resource")
def test_delete_file_client_error_returns_false(mock_resource):
    mock_obj = mock.Mock()
    mock_obj.delete.side_effect = ClientError({"Error": {"Code": "404", "Message": "Missing"}}, "Delete")
    mock_resource.return_value.Object.return_value = mock_obj
    s3 = S3Utils(bucket_name="bucket")

    assert s3.delete_file("file.jpg") is False
