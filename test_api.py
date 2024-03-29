import requests
import pytest_check as check
import pytest
from config import API_URL
import jsonschema
import time

# def get_api_status_code(service):
#     response = requests.request(API_URL + service)

response_gender_schema = {
    "type": "object",
    "properties": {
        "isSuccess": {"type": "boolean"},
        "errorCode": {"type": "integer"},
        "errorMessage": {"type": "string"},
        "idList": {"type": "array", "items": {"type": "integer"}}
    },
    "required": ["isSuccess", "errorCode"]
}

response_user_schema = {
    "type": "object",
    "properties": {
        "isSuccess": {"type": "boolean"},
        "errorCode": {"type": "integer", "format": "int32"},
        "errorMessage": {"type": "string"},
        "user": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "format": "int32"},
                "name": {"type": "string"},
                "gender": {"type": "string"},
                "age": {"type": "integer", "format": "int32"},
                "city": {"type": "string"},
                "registrationDate": {"type": "string", "format": "date-time"}
            },
            "required": ["id", "name", "gender", "age", "city", "registrationDate"]
        }
    },
    "required": ["isSuccess", "errorCode"]
}


def check_response_schema(response, schema):
    try:
        jsonschema.validate(response, schema)
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Response does not match schema: {e}")


def get_all_idlist():
    response = requests.get(API_URL + "users?gender=any")
    data = response.json()
    ids = data['idList']
    return ids


def get_idlist(gender):
    response = requests.get(API_URL + "users?gender=" + gender)
    data = response.json()
    ids = data['idList']
    return ids


def check_gender_by_id(gender_response, gender):
    result = []
    gender_json = gender_response.json()
    for user_id in gender_json['idList']:
        response = requests.get(API_URL + "user//" + str(user_id))
        data = response.json()
        user_gender = data['user']['gender']
        if user_gender != gender:
            result.append(f'Wrong gender for UserId: {user_id} - {user_gender} should be {gender}')
    check.equal(result, [], f'Users with wrong genders: \n{result}')


def check_userid(gender_response):
    gender_json = gender_response.json()
    result = []
    for user_id in gender_json['idList']:
        response = requests.get(API_URL + "user//" + str(user_id))
        data = response.json()
        user_data = data.get('user')
        if user_data is None:
            result.append(f'User ID : {user_id} has no data')
            continue
        getting_id = data['user']['id']
        if getting_id != user_id:
            result.append(f'Request UserId: {user_id} not equal response UserID: {getting_id} ')
    check.equal(result, [], f'Users with wrong IDs: \n{result}')


genders = [("male"), ("female"), ("any")]


@pytest.mark.parametrize("gender", genders)
class TestPositivesGenders:
    service_endpoint = "users?gender="

    def test_gender_service_available(self, gender):
        response = requests.get(API_URL + self.service_endpoint + gender)
        assert response.status_code == 200

    def test_gender_schema(self, gender):
        response = requests.get(API_URL + self.service_endpoint + gender)
        check_response_schema(response.json(), response_gender_schema)

    def test_gender_correct(self, gender):
        if gender == "any":
            pytest.skip("Skipping test for 'any' gender")
        response = requests.get(API_URL + self.service_endpoint + gender)
        check_gender_by_id(response, gender)

    def test_gender_service_request_time(self, gender):
        start_time = time.perf_counter()
        response = requests.get(API_URL + self.service_endpoint + gender)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        assert execution_time < 5

    def test_gender_request_limit(self, gender):
        num_requests = 10
        for _ in range(num_requests):
            response = requests.get(API_URL + self.service_endpoint + gender)
            assert response.status_code == 200


def test_gender_check_intersection():
    male_users = set(get_idlist("male"))
    female_users = set(get_idlist("female"))
    intersection_users = male_users.intersection(female_users)
    assert intersection_users == 0, f'intersection found between male and female users{intersection_users}'


def test_gender_check_ids_summ():
    all_users = set(get_idlist("any"))
    male_users = set(get_idlist("male"))
    female_users = set(get_idlist("female"))
    any_set = male_users.union(female_users)
    assert any_set == all_users


def test_gender_uppercase(service_endpoint="users?gender="):
    response = requests.get(API_URL + service_endpoint + "MALE")
    assert response.status_code == 200


def test_gender_wrong_method(service_endpoint="users?gender="):
    response = requests.post(API_URL + service_endpoint + "male")
    assert response.status_code == 405


wrong_genders = [(""), ("= "), ("=123"), ("=test")]


@pytest.mark.parametrize("gender", wrong_genders)
class TestNegativeGenders:
    service_endpoint = "users?gender"

    def test_gender_wrong_data(self, gender):
        response = requests.get(API_URL + self.service_endpoint + gender)
        assert response.status_code == 500


idList = [("5"), ("10"), ("15"), ("2"), ("10000")]


@pytest.mark.parametrize("userid", idList)
class TestUserIds:
    service_endpoint = "user//"

    def test_userdata_service_available(self, userid):
        response = requests.get(API_URL + self.service_endpoint + str(userid))
        assert response.status_code == 200

    def test_schema_userdata(self, userid):
        response = requests.get(API_URL + self.service_endpoint + str(userid))
        check_response_schema(response.json(), response_user_schema)

    def test_userdata_service_request_time(self, userid):
        start_time = time.perf_counter()
        response = requests.get(API_URL + self.service_endpoint + str(userid))
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        assert execution_time < 5

    def test_userdata_request_limit(self, userid):
        num_requests = 10
        for _ in range(num_requests):
            response = requests.get(API_URL + self.service_endpoint + str(userid))
            assert response.status_code == 200


wrong_user_id = [("0"), ("-1"), ("0,1"), ("test"), ("")]


@pytest.mark.parametrize("userid", wrong_user_id)
class TestNegativeUserId:
    service_endpoint = "user//"

    def test_userdata_wrong_data(self, userid):
        response = requests.get(API_URL + self.service_endpoint + str(userid))
        assert response.status_code == 400


def test_userdata_wrong_method(service_endpoint="user//"):
    response = requests.post(API_URL + service_endpoint + "5")
    assert response.status_code == 405


def test_userdata_correct(service_endpoint="users?gender="):
    response = requests.get(API_URL + service_endpoint + "any")
    check_userid(response)
